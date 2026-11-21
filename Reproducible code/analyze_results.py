import json
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
p=R/'final';df=pd.read_csv(p/'all_decisions.csv');s=pd.read_csv(p/'summary.csv')
ref='Starlight CP + Bonferroni';rf='Random forest + abstention'
# Replicate-level bootstrap: same 54 fixed settings per independent test batch
per=df.assign(loss=lambda x:np.where(x.outcome=='unsupported',20,np.where(x.outcome=='abstain',1,0)))\
      .groupby(['regime','rep','method']).agg(loss=('loss','mean'),correct=('outcome',lambda x:(x=='correct').mean()),wrong=('outcome',lambda x:(x=='unsupported').mean()),abstain=('outcome',lambda x:(x=='abstain').mean())).reset_index()
rows=[];rng=np.random.default_rng(20261121)
for regime in ['baseline','nonlinear','heavy_tail','model_break','small_effect','exact_tie']:
    xx=per[per.regime==regime].pivot(index='rep',columns='method',values='loss')
    diff=(xx[ref]-xx[rf]).to_numpy()
    idx=rng.integers(0,len(diff),(8000,len(diff)))
    bounds=np.quantile(diff[idx].mean(1),[.025,.975])
    rows.append(dict(regime=regime,starlight_mean_loss=xx[ref].mean(),rf_selective_mean_loss=xx[rf].mean(),
                     mean_loss_diff_starlight_minus_rf=diff.mean(),ci_low=bounds[0],ci_high=bounds[1]))
pd.DataFrame(rows).to_csv(p/'paired_bootstrap_uncertainty.csv',index=False)
# Risk sensitivity across known arbitrary penalties
cost=[]
for _,r in s.iterrows():
    for pen in [1,2,5,10,20,50,100]:
        cost.append(dict(regime=r.regime,method=r.method,wrong_to_abstain_cost_ratio=pen,
                         hypothetical_cost=(pen*r.unsupported+r.abstain)/(r.correct+r.unsupported+r.abstain)))
pd.DataFrame(cost).to_csv(p/'decision_cost_sensitivity.csv',index=False)
# cross training seeds variation, batch summaries
seeds=[]
for name in ['final','seed_20261122','seed_20261123']:
    a=pd.read_csv(R/name/'summary.csv')
    a['run']=name;seeds.append(a)
pd.concat(seeds,ignore_index=True).to_csv(p/'three_seed_sensitivity.csv',index=False)
# summarize reproducible results
summary=s.pivot(index='regime',columns='method',values='illustrative_loss')
print('Paired bootstrap: Starlight minus RF-selective 20:1 loss')
print(pd.DataFrame(rows).to_string(index=False,float_format=lambda v:format(v,'.4f')))
print('\nLoss average over arbitrarily equally weighted six regimes:')
print(s.groupby('method').illustrative_loss.mean().sort_values().round(3))
# Post-hoc RF threshold sweep is a *diagnostic*, NOT a tuned competing model.
base=df[df.method=='Random forest']
thresholds=[0,.01,.02,.03,.05,.075,.1,.12,.141762211,.16,.2,.25,.3]
rows=[]
for regime,group in base.groupby('regime'):
    scores=group.rf_predicted_delta.to_numpy(); truth=group.true_sign.to_numpy()
    for threshold in thresholds:
        select=np.abs(scores)>threshold
        wrong=(np.sign(scores[select])!=truth[select]).sum()
        right=select.sum()-wrong
        abst=(~select).sum()
        rows.append({'regime':regime,'threshold':threshold,'selected':int(select.sum()),
                     'correct':int(right),'unsupported':int(wrong),'abstained':int(abst),
                     'selection_pct':100*select.mean(),
                     'wrong_all_pct':100*wrong/len(select),
                     'illustrative_cost':(20*wrong+abst)/len(select)})
pd.DataFrame(rows).to_csv(p/'RF_posthoc_risk_coverage_sweep.csv',index=False)
print('\nPosthoc RF diagnostic, best test-set costs (unfair to call as prospective results):')
for regime,group in pd.DataFrame(rows).groupby('regime'):
    a=group.loc[group.illustrative_cost.idxmin()]
    print(regime,'threshold',round(a.threshold,3),'cost',round(a.illustrative_cost,3),'selected',round(a.selection_pct,1),'wrong',round(a.wrong_all_pct,2))
# Risk coverage plots for baseline and shift, with Starlight marked. Illustrative, no special palette.
fig,axs=plt.subplots(1,3,figsize=(15,4.8))
for ax,regime in zip(axs,['baseline','model_break','small_effect']):
    z=pd.DataFrame(rows);z=z[z.regime==regime]
    ax.plot(z.selection_pct,z.wrong_all_pct,marker='o',label='RF + thresholds (post hoc)')
    w=s[(s.regime==regime)&(s.method==ref)].iloc[0]
    ax.scatter([w.selection_pct],[w.unsupported_per_100],marker='*',s=120,label='Starlight')
    ax.set_xlabel('Selection rate (%)');ax.set_ylabel('Unsupported calls per 100 decisions (%)')
    ax.set_title(regime.replace('_',' ').title());ax.grid(alpha=.3);ax.legend(fontsize=8)
fig.suptitle('Diagnostic tradeoff: RF threshold sweep chosen AFTER test (not valid for claiming superiority)')
fig.tight_layout();fig.savefig(p/'RF_risk_coverage_diagnostic.png',dpi=160);plt.close(fig)
