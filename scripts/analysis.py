"""Derived analyses; no outcome-dependent changes to experiment settings."""
from pathlib import Path
import json,shutil,math,itertools,hashlib,sys
import numpy as np
import pandas as pd
from scipy.stats import beta,multinomial
from experiment import R,simultaneous,paired,bank
def region_summary(d):
    pos=d[d.lower>0];neg=d[d.upper<0]
    status='NON-ROBUST' if len(pos) and len(neg) else ('A-UNIFORM' if len(pos)==len(d) else ('D-UNIFORM' if len(neg)==len(d) else 'UNRESOLVED'))
    return dict(K=len(d),A=len(pos),D=len(neg),U=len(d)-len(pos)-len(neg),status=status,min_estimate=float(d.delta.min()),max_estimate=float(d.delta.max()),minimum_lower=float(d.lower.min()),maximum_upper=float(d.upper.max()))
def bootstrap(v,seed=202610034):
    vals,c=np.unique(v,return_counts=True);b=np.random.default_rng(seed).multinomial(len(v),c/len(v),50000)@vals/len(v)
    return b
def pre():
    old=R.parent/'IRIS_Starlight_Research';(R/'data/historical').mkdir(exist_ok=True)
    for source,name in [(old/'results/specifications.csv','archived_32_counts.csv'),(old/'data/physical_timing_records.csv','physical_timing_records.csv'),(old/'results/timing.csv','timing.csv'),(old/'results/timing_subgroups.csv','timing_subgroups.csv'),(old/'results/source_audit.csv','source_audit.csv'),(old/'data/physical_failure_method_matrix.csv','physical_failure_method_matrix.csv'),(old/'results/fresh_results.csv','earlier_fresh_results.csv'),(old/'data/fresh_missions.csv.gz','earlier_fresh_missions.csv.gz'),(old/'data/random_seeds.txt','earlier_seed_manifest.csv')]:shutil.copy2(source,R/'data/historical'/name)
    archive=pd.read_csv(old/'results/specifications.csv');rows=[]
    for _,r in archive.iterrows():
        n=int(r.N);plus=int(r.plus);minus=int(r.minus);both=int(r.both_fail)
        a=np.r_[np.zeros(plus),np.ones(minus),np.ones(both),np.zeros(n-plus-minus-both)]
        d=np.r_[np.ones(plus),np.zeros(minus),np.ones(both),np.zeros(n-plus-minus-both)]
        rows.append(dict(s=r.s,g=r.gain,dt=r['dt'],**simultaneous(a,d,32,.05)))
    a=pd.DataFrame(rows);a.to_csv(R/'results/archived_simultaneous.csv',index=False)
    source=R.parents[1]/'Starlight_Physical_Evidence_Reconstruction'
    for name in ['steering_calibration.csv','physical_trajectories.csv','trajectory_qc_report.md','cohort_completeness_audit.md','video_evidence_manifest.csv','retained_video_failure_events.csv']:
        shutil.copy2(source/name,R/'evidence'/name)
    shutil.copy2(source/'evidence/trajectory_feasibility_diagnostic.json',R/'evidence/trajectory_feasibility_diagnostic.json')
    shutil.copy2(source/'evidence/repository/src/drive.py',R/'evidence/historical_drive.py')
    # Exact finite enumeration of a small-N marginal interval: numerical sanity check, not the proof.
    n=30;alpha=.05;tail=alpha/4;counts=[];lo=[];hi=[]
    def cp(k):return (0 if k==0 else beta.ppf(tail,k,n-k+1),1 if k==n else beta.ppf(1-tail,k+1,n-k))
    for p in range(n+1):
        for m in range(n+1-p):
            pl,pu=cp(p);ml,mu=cp(m);counts.append([p,m,n-p-m]);lo.append(pl-mu);hi.append(pu-ml)
    counts=np.array(counts);lo=np.array(lo);hi=np.array(hi);out=[]
    for pp,pm in [(0,0),(.005,.001),(.01,.01),(.1,.02),(.2,.2),(.6,.1),(.95,.01),(.5,.5)]:
        mass=multinomial.pmf(counts,n,[pp,pm,1-pp-pm]);delta=pp-pm;cov=float(mass[(lo<=delta)&(hi>=delta)].sum());out.append(dict(n=n,p_plus=pp,p_minus=pm,coverage=cov));assert cov>=.95-1e-12
    pd.DataFrame(out).to_csv(R/'results/coverage_enumeration.csv',index=False)
    print('Archived interval summary (retrospective only):',region_summary(a));print('Enumerated coverage:',min(x['coverage'] for x in out))
def post():
    p=json.loads((R/'protocol/frozen_protocol.json').read_text());grid=pd.read_csv(R/'results/grid.csv');forms=pd.read_csv(R/'results/forms.csv');confirm=pd.read_csv(R/'results/confirmation.csv');ext=pd.read_csv(R/'results/cartpole.csv')
    summary={name:region_summary(d) for name,d in [('grid',grid),('confirmation',confirm),('cartpole',ext)]}
    summary['forms']={name:region_summary(x) for name,x in forms.groupby('form')}
    # Functional ANOVA of a uniformly weighted, fully crossed finite grid. Descriptive only.
    factors=['g','s','dt'];grand=grid.delta.mean();main={k:grid.groupby(k).delta.mean()-grand for k in factors};terms={};center=grid.delta.to_numpy()-grand
    for k in factors:terms[k]=grid[k].map(main[k]).to_numpy()
    for a,b in itertools.combinations(factors,2):
        group=grid.groupby([a,b]).delta.mean()
        terms[a+' x '+b]=np.array([group.loc[(r[a],r[b])]-grand-main[a].loc[r[a]]-main[b].loc[r[b]] for _,r in grid.iterrows()])
    terms['g x s x dt']=center-sum(terms.values());total=float(np.mean(center**2))
    rows=[dict(component=k,mean_square=float(np.mean(v*v)),fraction=float(np.mean(v*v)/total)) for k,v in terms.items()]
    assert abs(sum(x['fraction'] for x in rows)-1)<1e-8
    pd.DataFrame(rows).to_csv(R/'results/attribution.csv',index=False)
    # Preserved paired parameter contrasts at fixed s or dt.
    taskmap={(t['g'],t['s'],t['dt']):t for t in p['tasks'] if t['family']=='grid'};contrasts=[]
    for s in [.015,.03,.05]:
        for dt in [.01,.04]:
            a0,d0=paired(taskmap[1.2,s,dt]);a1,d1=paired(taskmap[1.3,s,dt]);v=(d1-a1)-(d0-a0);ci=np.quantile(bootstrap(v),[.025,.975]);contrasts.append(dict(s=s,dt=dt,contrast='gain 1.3 minus gain 1.2',change=float(v.mean()),lo=ci[0],hi=ci[1]))
    pd.DataFrame(contrasts).to_csv(R/'results/paired_attribution_contrasts.csv',index=False)
    # Finite-search witnesses and valid upper bound conditional on confirmed positive nominal.
    c=confirm.copy();c['distance']=np.sqrt(((c.g-1.2)/.1)**2+((c.s-.03)/.035)**2+((c.dt-.04)/.03)**2)
    nominal=c[(c.g==1.2)&(c.s==.03)&(c.dt==.04)].iloc[0];negative=c[c.upper<0].sort_values('distance')
    summary['fragility']=dict(norm='L2',scales=[.1,.035,.03],nominal_confirmed=bool(nominal.lower>0),upper_bound=float(negative.iloc[0].distance) if nominal.lower>0 and len(negative) else None,witness=negative.iloc[0].to_dict() if len(negative) else None)
    # Known finite-set extremal expectations lie in [min lower,min upper], [max lower,max upper].
    summary['finite_extrema']=dict(min_interval=[float(grid.lower.min()),float(grid.upper.min())],max_interval=[float(grid.lower.max()),float(grid.upper.max())],continuous_extrema='Not bounded by this finite grid')
    nominaltask=taskmap[1.2,.03,.04];a,d=paired(nominaltask)
    ident=simultaneous(a,a,1,.05);swapped=simultaneous(d,a,66,.02);orig=simultaneous(a,d,66,.02)
    assert abs(swapped['delta']+orig['delta'])<1e-15 and abs(swapped['lower']+orig['upper'])<1e-12
    rng=np.random.default_rng(202610035);v=d-a;random_results=[]
    for i in range(1000):
        flip=rng.integers(0,2,len(a)).astype(bool);aa=np.where(flip,d,a);dd=np.where(flip,a,d);r=simultaneous(aa,dd,1,.05);random_results.append(dict(repetition=i,delta=r['delta'],lower=r['lower'],upper=r['upper'],region=r['region']))
    pd.DataFrame(random_results).to_csv(R/'results/random_label_controls.csv',index=False)
    old=pd.read_csv(R/'data/historical/earlier_fresh_missions.csv.gz');old=old[old.gain==1.2];ao=1-old[old.architecture=='A'].sort_values('bank_index').mission_success.to_numpy();do=1-old[old.architecture=='D'].sort_values('bank_index').mission_success.to_numpy()
    difference=bootstrap(v,3)-bootstrap(do-ao,4);ci=np.quantile(difference,[.025,.975])
    ctrl=dict(identical_AA=ident,global_label_swap_exact=True,random_label_repetitions=1000,random_label_sign_exclusions=sum(x['region']!='U' for x in random_results),random_label_mean=float(np.mean([x['delta'] for x in random_results])),independent_bank_change=float(v.mean()-(do-ao).mean()),independent_bank_change_pointwise_ci=ci.tolist())
    # Actual repeat-execution / metadata invariance check on 20 withheld seeds.
    sys.path.insert(0,str(R/'code/models'));from base.mission import simulate
    repeated=[]
    for seed in range(20269900,20269920):
        x=simulate(seed,'A',np.zeros(10));y=simulate(seed,'A',np.zeros(10));x['bookkeeping']='first';y['bookkeeping']='renamed'
        repeated.append(x['failure_code']==y['failure_code'] and x['duration']==y['duration'])
    assert all(repeated);ctrl['repeat_execution_pairs']=20;ctrl['metadata_invariance']=all(repeated)
    (R/'results/negative_controls.json').write_text(json.dumps(ctrl,indent=2))
    # Master-bank seed audit, including previous production/fresh banks.
    banks={str(master):set(bank(master,n)[0].tolist()) for master,n in [(202610031,4000),(202610032,8000)]}
    banks['prior_production']=set(pd.read_csv(R/'data/historical/earlier_seed_manifest.csv').scenario_seed)
    banks['prior_fresh']=set(old.scenario_seed)
    overlaps={a+' vs '+b:len(banks[a]&banks[b]) for a,b in itertools.combinations(banks,2)}
    summary['seed_overlaps']=overlaps
    summary['spread_pp']=100*float(grid.delta.max()-grid.delta.min());summary['median_simultaneous_width_pp']=100*float((grid.upper-grid.lower).median());summary['scale_ratio']=summary['spread_pp']/summary['median_simultaneous_width_pp']
    summary['sampling_resolution_N_at_gamma_001']=math.ceil(8*math.log(2*66/.02)/.01**2)
    (R/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print('Controls:',ctrl)
if __name__=='__main__':{'pre':pre,'post':post}[sys.argv[1]]()
