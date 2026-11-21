#!/usr/bin/env python3
"""Honest synthetic evaluation of Starlight's paired CP/Bonferroni certificate vs ML.

NOT the original 752,000-mission Starlight simulator. Source archive lacks its generator.
Contains Gaussian and heavy-tail regimes with analytic ground truth; no real robotics validation.
Generated 2026-11-21. Decision scoring and tuning must be fixed before test evaluation.
"""
import argparse, json, os, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm,beta
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import torch
from torch import nn

# Reproducible CPU behavior
os.environ['OMP_NUM_THREADS']='1';torch.set_num_threads(1)
T=0.080; PVT=0.28; NBINS=24; EDGES=np.linspace(-.35,.35,NBINS+1)
G_LIST=np.linspace(1.200,1.300,9); S_LIST=[.026,.035,.050]; DT_LIST=[.010,.040]
SETTINGS=np.array([[g,s,dt] for s in S_LIST for dt in DT_LIST for g in G_LIST],dtype=float)
ALPHA=.05


def model_params(g,s,dt,regime):
    """A declared *toy* terminal yaw-error surrogate; not an Ackermann digital twin."""
    ga=np.asarray(g);ss=np.asarray(s);tt=np.asarray(dt)
    ma=.82*(ga/1.207-1)+.010*(tt-.025)/.015
    md=.82*(ga/1.283-1)-.006*(tt-.025)/.015
    sd=ss*(1+.18*(tt-.01)/.03)
    mix=0.
    if regime=='nonlinear':
        ma=ma+.034*np.exp(-((ga-1.256)/.011)**2)
        md=md-.023*np.exp(-((ga-1.224)/.013)**2)
    elif regime=='heavy_tail':
        sd=sd*1.15;mix=.08
        ma=ma+.018*np.exp(-((ga-1.250)/.017)**2)
    elif regime=='model_break':
        # previously unobserved actuator model with localized non-monotone bias
        ma=ma+.060*np.sin((ga-1.200)*np.pi/.055)
        md=md-.034*np.exp(-((ga-1.257)/.012)**2)
    elif regime=='small_effect':
        # Small modeled advantage resembling the ~1-3 pp scale in the Starlight confirmation.
        # It is NOT calibrated to its empirical simulator, and includes exact crossing points.
        md=ma+.006*np.sin((ga-1.200)*np.pi/.10)
    elif regime=='exact_tie':
        md=ma
    return ma,md,sd,mix


def p_fail(mu,sd,mix=0.):
    def term(sig):
        return norm.cdf((-T-mu)/sig)+norm.sf((T-mu)/sig)
    s=sd*np.sqrt(1+PVT**2)
    # In outlier draws ONLY the common disturbance is multiplied by 3; private noise is not.
    # Hence the tail SD is sd*sqrt(3^2 + PVT^2), NOT 3*s.
    s_tail=sd*np.sqrt(9+PVT**2)
    return (1-mix)*term(s)+mix*term(s_tail)


def oracle_delta(g,s,dt,regime):
    ma,md,sd,q=model_params(g,s,dt,regime)
    return p_fail(md,sd,q)-p_fail(ma,sd,q)


def simulate_one(rng,setting,n,regime):
    g,s,dt=setting
    ma,md,sd,q=model_params(g,s,dt,regime)
    z=rng.standard_normal(n)
    if q>0:
        z=np.where(rng.random(n)<q,3*z,z)
    ea=ma+sd*(z+PVT*rng.standard_normal(n))
    ed=md+sd*(z+PVT*rng.standard_normal(n))
    ya=(np.abs(ea)>T).astype(np.int8)
    yd=(np.abs(ed)>T).astype(np.int8)
    return ea,ed,ya,yd


def make_features(setting,ea,ed,ya,yd):
    g,s,dt=setting
    x=(yd-ya).astype(np.int16)
    hA=np.histogram(ea,bins=EDGES)[0]/len(ea)
    hD=np.histogram(ed,bins=EDGES)[0]/len(ed)
    feats=np.array([g,s,dt,ya.mean(),yd.mean(),np.mean(x==1),np.mean(x==-1),
          np.mean(ea),np.mean(ed),np.std(ea),np.std(ed),np.mean(ea*ed)],dtype='float32')
    return feats, np.stack([hA,hD]).astype('float32'), float(np.mean(x)), int((x==1).sum()),int((x==-1).sum())


def cp_interval(pos,neg,n,k=54,alpha=.05):
    eta=alpha/(2*k)
    def bounds(c):
        l=0. if c==0 else beta.ppf(eta/2,c,n-c+1)
        u=1. if c==n else beta.ppf(1-eta/2,c+1,n-c)
        return l,u
    a,b=bounds(pos);c,d=bounds(neg)
    return a-d,b-c


def training_dataset(rng,count,n,regime='baseline'):
    nums=[]; hists=[]; obs=[]; mus=[]; sds=[];truth=[]
    for i in range(count):
        g=rng.uniform(1.195,1.305);s=rng.uniform(.023,.053);dt=rng.choice(DT_LIST)
        r=regime if regime!='mixed_validation' else rng.choice(['baseline','nonlinear','heavy_tail','exact_tie'],p=[.3,.2,.2,.3])
        eA,eD,yA,yD=simulate_one(rng,[g,s,dt],n,r)
        f,h,z,*_=make_features([g,s,dt],eA,eD,yA,yD)
        nums.append(f);hists.append(h);obs.append(z)
        mus.append([eA.mean(),eD.mean()]);sds.append(np.mean([eA.std(),eD.std()])/np.sqrt(1+PVT**2));truth.append(float(oracle_delta(g,s,dt,r)))
    return np.asarray(nums),np.asarray(hists),np.asarray(obs),np.asarray(mus),np.asarray(sds),np.asarray(truth)


class CNN(nn.Module):
    def __init__(self,p):
        super().__init__()
        self.conv=nn.Sequential(nn.Conv1d(2,16,3,padding=1),nn.ReLU(),
                                nn.Conv1d(16,16,3,padding=1),nn.ReLU(),
                                nn.AdaptiveAvgPool1d(6),nn.Flatten())
        self.mlp=nn.Sequential(nn.Linear(16*6+p,64),nn.ReLU(),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,1))
    def forward(self,h,n):return self.mlp(torch.cat([self.conv(h),n],dim=1)).flatten()

class PINN(nn.Module):
    """Physics-informed network for mean angular error and noise scale.
    Penalizes mismatch to first-order steering-response d(error)/dg ~ .82/g_ref.
    This is a physics-informed simplified surrogate, not a vehicle PDE solver.
    """
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(3,32),nn.Tanh(),nn.Linear(32,32),nn.Tanh(),nn.Linear(32,3))
    def forward(self,x):return self.net(x)


def train_cnn(ntr,htr,ytr,nva,hva,yva,seed,epochs=85):
    torch.manual_seed(seed)
    xm=ntr.mean(0);xs=ntr.std(0)+1e-5
    x=torch.tensor((ntr-xm)/xs);h=torch.tensor(htr);t=torch.tensor(ytr,dtype=torch.float32)
    xv=torch.tensor((nva-xm)/xs);hv=torch.tensor(hva);tv=torch.tensor(yva,dtype=torch.float32)
    net=CNN(x.shape[1]);opt=torch.optim.Adam(net.parameters(),lr=.003,weight_decay=.0005)
    best=1e10;beststate=None;patience=0
    for ep in range(epochs):
        net.train()
        for ids in torch.randperm(len(x)).split(128):
            loss=((net(h[ids],x[ids])-t[ids])**2).mean()
            opt.zero_grad();loss.backward();opt.step()
        net.eval()
        with torch.no_grad(): val=((net(hv,xv)-tv)**2).mean().item()
        if val<best-1e-7:
            best=val;beststate={k:v.detach().clone() for k,v in net.state_dict().items()};patience=0
        else:patience+=1
        if patience>12:break
    net.load_state_dict(beststate);net.eval()
    def predict(nums,hists):
        with torch.no_grad():
            return net(torch.tensor(hists,dtype=torch.float32),torch.tensor((nums-xm)/xs,dtype=torch.float32)).numpy()
    return predict,best


def train_pinn(ntr,mus,sds,nva,musval,sdsval,seed,epochs=300):
    torch.manual_seed(seed)
    # Normalize feature vector g,s,dt to [order 1] preserving derivative scale for g.
    X=ntr[:,:3].astype('float32');XX=nva[:,:3].astype('float32')
    mean=np.array([1.25,.0375,.025],dtype='float32');scale=np.array([.05,.018,.015],dtype='float32')
    x=torch.tensor((X-mean)/scale); xv=torch.tensor((XX-mean)/scale)
    target=np.concatenate([mus,np.log(sds[:,None])],axis=1).astype('float32')
    vtarget=np.concatenate([musval,np.log(sdsval[:,None])],axis=1).astype('float32')
    y=torch.tensor(target);vy=torch.tensor(vtarget)
    net=PINN();opt=torch.optim.Adam(net.parameters(),lr=.005,weight_decay=1e-5)
    best=1e9;beststate=None;patience=0
    # derivative d mu / d ((g-1.25)/.05) expected .05*.82 / g_reference
    deriv=torch.tensor([.05*.82/1.207,.05*.82/1.283])
    for ep in range(epochs):
        net.train(); ix=torch.randperm(len(x))[:512]
        batch=x[ix].detach().clone().requires_grad_(True)
        pred=net(batch)
        # Correctly weights log-scale relative to angular-error units.
        fit=((pred[:,:2]-y[ix,:2])**2).mean() + .001*((pred[:,2]-y[ix,2])**2).mean()
        physics=[]
        for j in range(2):
            grad=torch.autograd.grad(pred[:,j].sum(),batch,create_graph=True,retain_graph=True)[0][:,0]
            physics.append(((grad-deriv[j])**2).mean())
        loss=fit+.035*sum(physics)
        opt.zero_grad();loss.backward();opt.step()
        net.eval()
        with torch.no_grad():
            p=net(xv);val=((p[:,:2]-vy[:,:2])**2).mean()+.001*((p[:,2]-vy[:,2])**2).mean()
            val=val.item()
        if val<best-1e-8:best=val;beststate={k:v.detach().clone() for k,v in net.state_dict().items()};patience=0
        else:patience+=1
        if patience>30:break
    net.load_state_dict(beststate);net.eval()
    def predict(nums,hists):
        xv=torch.tensor((nums[:,:3]-mean)/scale,dtype=torch.float32)
        with torch.no_grad():
            z=net(xv).numpy()
        ma,md=z[:,0],z[:,1];sd=np.clip(np.exp(z[:,2]),.002,.2)
        return p_fail(md,sd)-p_fail(ma,sd)
    return predict,best


def tune_abstention(pred,true):
    """Validation-only 95% absolute-residual guard band.
    If validation and future tasks were exchangeable, split-conformal intervals
    for the *known true risk difference* have marginal coverage. With OOD
    test regimes and different task grids this is NOT a coverage guarantee.
    """
    residual=np.abs(pred-true)
    n=len(residual)
    rank=min(n,max(1,int(np.ceil((n+1)*.95))))
    q=float(np.sort(residual)[rank-1])
    selected=int(np.sum(np.abs(pred)>q))
    return q,selected


def main(args):
    t0=time.time();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    # Training and model selection ONLY on independent baseline tasks.
    tr=training_dataset(rng,args.train_tasks,args.train_pairs)
    va=training_dataset(rng,args.val_tasks,args.train_pairs,regime='mixed_validation')
    tn,th,ty,tm,ts,_=tr;vn,vh,vy,vm,vs,oracle_val=va
    log=make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=2000))
    lglabels=np.where(ty>=0,1,0)
    log.fit(tn,lglabels)
    rf=RandomForestRegressor(n_estimators=140,max_depth=10,min_samples_leaf=5,
                             max_features=.85,n_jobs=1,random_state=args.seed)
    rf.fit(tn,ty)
    cnnpred,cnn_val=train_cnn(tn,th,ty,vn,vh,vy,args.seed)
    pinnpred,pinn_val=train_pinn(tn,tm,ts,vn,vm,vs,args.seed)
    # RF abstention margin calibrated using independent oracle-labelled synthetic validation tasks.
    # Calculate exact deltas using the validation task contexts, not the observed sample labels.
    # Mixed validation has known synthetic truth; OOD 'model_break' remains unseen.
    abst_thr,valid_selected=tune_abstention(rf.predict(vn),oracle_val)
    models=['Starlight CP + Bonferroni','CNN (1D error histogram)','PINN (physics-informed response)',
            'Random forest + abstention','Logistic regression','Random forest','Raw failure difference']
    # Full-grid simultaneous CP covers all 54 gain-stress-dt settings in a replicate.
    k=len(SETTINGS);records=[]
    truth=[]
    for regime in ['baseline','nonlinear','heavy_tail','model_break','small_effect','exact_tie']:
        true=oracle_delta(SETTINGS[:,0],SETTINGS[:,1],SETTINGS[:,2],regime)
        for j,(setting,d) in enumerate(zip(SETTINGS,true)):
            truth.append({'regime':regime,'cell':j,'gain':setting[0],'stress':setting[1],
                          'dt':setting[2],'true_delta_pp':100*float(d)})
        for rep in range(args.reps):
            nums=[];hists=[];raw=[];intervals=[]
            for setting in SETTINGS:
                eA,eD,yA,yD=simulate_one(rng,setting,args.test_pairs,regime)
                num,h,delta,pos,neg=make_features(setting,eA,eD,yA,yD)
                lo,hi=cp_interval(pos,neg,args.test_pairs,k=k)
                nums.append(num);hists.append(h);raw.append(delta);intervals.append([lo,hi])
            nums=np.stack(nums);hists=np.stack(hists);raw=np.array(raw);intervals=np.array(intervals)
            rf_pred=rf.predict(nums)
            cnn_scores=cnnpred(nums,hists)
            pinn_scores=pinnpred(nums,hists)
            logistic_probs=log.predict_proba(nums)[:,1]
            results={
              models[0]:np.where(intervals[:,0]>0,1,np.where(intervals[:,1]<0,-1,0)),
              models[1]:np.sign(cnn_scores).astype(int),
              models[2]:np.sign(pinn_scores).astype(int),
              models[3]:np.where(np.abs(rf_pred)>abst_thr,np.sign(rf_pred),0).astype(int),
              models[4]:np.where(logistic_probs>.5,1,-1),
              models[5]:np.sign(rf_pred).astype(int),
              models[6]:np.where(raw>=0,1,-1),
            }
            # Also ensure *true* exact-tie is treated as equality in score.
            true_dir=np.sign(true).astype(int)
            true_dir[np.abs(true)<1e-12]=0
            for name,decision in results.items():
                for cell,(dec,gt) in enumerate(zip(decision,true_dir)):
                    state='abstain' if dec==0 else ('correct' if dec==gt else 'unsupported')
                    records.append((regime,rep,cell,name,int(dec),int(gt),state,float(rf_pred[cell]),float(raw[cell])))
            if rep==0:
                df=pd.DataFrame({'regime':regime,'gain':SETTINGS[:,0],
                                 'stress':SETTINGS[:,1],'dt':SETTINGS[:,2],
                                 'truth_delta_pp':100*true,'observed_delta_pp':100*raw,
                                 'CP_lower_pp':100*intervals[:,0],'CP_upper_pp':100*intervals[:,1]})
                df.to_csv(out/f'first_rep_{regime}.csv',index=False)
        print('Finished',regime,flush=True)
    df=pd.DataFrame(records,columns=['regime','rep','cell','method','decision','true_sign','outcome','rf_predicted_delta','raw_observed_delta'])
    df.to_csv(out/'all_decisions.csv',index=False)
    pd.DataFrame(truth).to_csv(out/'oracle_truth.csv',index=False)
    agg=df.groupby(['regime','method','outcome']).size().unstack(fill_value=0)
    for col in ['correct','unsupported','abstain']:
        if col not in agg:agg[col]=0
    agg['n']=agg[['correct','unsupported','abstain']].sum(axis=1)
    agg['selection_pct']=100*(agg['correct']+agg['unsupported'])/agg['n']
    agg['unsupported_per_100']=100*agg['unsupported']/agg['n']
    agg['wrong_per_100_selected']=100*agg['unsupported']/(agg['correct']+agg['unsupported']).clip(lower=1)
    # Explicit, arbitrary example decision loss with false winner 20x abstention.
    agg['illustrative_loss']=(20*agg['unsupported']+agg['abstain'])/agg['n']
    agg.reset_index().to_csv(out/'summary.csv',index=False)
    # uncertainty across independently generated pilot replicates (no treating decisions as independent)
    perrep=df.groupby(['regime','method','rep','outcome']).size().unstack(fill_value=0)
    for col in ['correct','unsupported','abstain']:
        if col not in perrep:perrep[col]=0
    perrep['error_pct']=100*perrep['unsupported']/k
    perrep['coverage_pct']=100*(perrep['correct']+perrep['unsupported'])/k
    rs=perrep.groupby(['regime','method'])[['error_pct','coverage_pct']].agg(['mean','std'])
    rs.to_csv(out/'replicate_uncertainty.csv')
    # show useful direct result graph, no decorative chart
    fig,axes=plt.subplots(3,2,figsize=(15,12),sharex=True,sharey=True)
    for ax,regime in zip(axes.ravel(),['baseline','nonlinear','heavy_tail','model_break','small_effect','exact_tie']):
        a=agg.loc[regime].reindex(models)
        y=np.arange(len(models)); left=np.zeros(len(models))
        for col in ['correct','unsupported','abstain']:
            val=100*a[col]/a['n']
            ax.barh(y,val,left=left,label=col)
            left=left+val.to_numpy()
        ax.set_title(regime.replace('_',' ').title());ax.set_xlim(0,100)
        ax.set_yticks(y,models,fontsize=9);ax.invert_yaxis();ax.set_xlabel('Percent of decisions')
        ax.grid(axis='x',alpha=.2)
    axes[0,0].legend(loc='lower right');fig.suptitle('NEW SYNTHETIC STUDY (not Starlight mission data)',fontsize=15)
    fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(out/'method_comparison.png',dpi=160);plt.close(fig)
    # Optional risk coverage curve plot for deciding vs cost
    cfg={'random_seed':args.seed,'train_tasks':args.train_tasks,'train_pairs':args.train_pairs,
         'validation_tasks':args.val_tasks,'test_pairs_per_cell':args.test_pairs,
         'test_repetitions':args.reps,'cells_per_regime':k,'family_alpha':ALPHA,
         'random_forest_abstention_threshold':abst_thr,'RF_val_selection_count':valid_selected,'RF_margin_calibration':'split 95% quantile of abs(predicted minus exact toy truth); OOD lacks coverage',
         'benchmark_methods':models,'source_simulator':'declared synthetic terminal-error model, NOT original Starlight generator',
         'neural_validation_losses':{'CNN':cnn_val,'PINN':pinn_val},'elapsed_seconds':time.time()-t0,
         'limitations':['ML trained with extra historical paired simulations (report training cost)',
                        'PINN assumes approximate first-order steering response; not a full-vehicle PINN',
                        'CNN is a 1D error-histogram CNN, not an image-perception CNN',
                        'RF abstention uses independent toy oracle residual calibration; no conditional/OOD guarantee',
                        'No ML confidence guarantee is established',
                        'All six regimes are synthetic and selected by experiment author',
                        'Exact truth is available only because simulator probabilities are explicitly known',
                        'No original A/D simulator, no hardware validation or real-world savings']}
    with open(out/'settings.json','w') as f:json.dump(cfg,f,indent=2)
    print(agg[['correct','unsupported','abstain','selection_pct','illustrative_loss']].round(2).to_string())
    print('Output',out,'time',round(time.time()-t0,1))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=20261121)
    p.add_argument('--train-tasks',type=int,default=1800)
    p.add_argument('--val-tasks',type=int,default=500)
    p.add_argument('--train-pairs',type=int,default=400)
    p.add_argument('--test-pairs',type=int,default=700)
    p.add_argument('--reps',type=int,default=30)
    p.add_argument('--out',default=str(Path(__file__).resolve().parent))
    args=p.parse_args();main(args)
