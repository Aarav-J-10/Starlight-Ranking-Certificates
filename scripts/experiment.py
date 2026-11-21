"""Frozen, fixed-size Starlight experiment and independent confirmation."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import beta
import sys,json,hashlib,shutil,datetime,importlib,time
from concurrent.futures import ProcessPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'code/models'))
NAMES=('illumination','ambiguity','camera_pitch','camera_offset','sensor_noise','latency','steering_offset','steering_lag','battery_loss','slip')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def simultaneous(a,d,K,alpha):
    a=np.asarray(a);d=np.asarray(d);v=d-a;n=len(v)
    plus=int(sum(v==1));minus=int(sum(v==-1))
    tail=alpha/(4*K)
    def cp(x):return (0. if x==0 else float(beta.ppf(tail,x,n-x+1)),1. if x==n else float(beta.ppf(1-tail,x+1,n-x)))
    pl,pu=cp(plus);ml,mu=cp(minus);lo=pl-mu;hi=pu-ml
    eps=float(np.sqrt(2*np.log(2*K/alpha)/n))
    return dict(N=n,plus=plus,minus=minus,A_failure=float(a.mean()),D_failure=float(d.mean()),delta=float(v.mean()),lower=lo,upper=hi,hoeffding_lower=max(-1,float(v.mean())-eps),hoeffding_upper=min(1,float(v.mean())+eps),region='A' if lo>0 else ('D' if hi<0 else 'U'),K=K,alpha=alpha)
def bank(master,n):
    seeds=np.random.default_rng(np.random.SeedSequence([master,0])).integers(1,2**31-1,n)
    u=np.random.default_rng(np.random.SeedSequence([master,1])).random((n,10))
    w=np.random.default_rng(np.random.SeedSequence([master,2])).random((n,10))
    assert len(set(seeds))==n
    return seeds,u,w
def cell(task):
    key=task['id'];dest=R/'data/new'/f'{key}.csv.gz'
    if dest.exists():return key+' retained'
    module='base' if task['form']=='triangular' else task['form']
    simulate=importlib.import_module(module+'.mission').simulate
    seeds,u,w=bank(task['master'],task['n'])
    z=(u+w)/2 if task['form']=='triangular' else u.copy()
    z[:,[2,3,6]]=2*z[:,[2,3,6]]-1;z*=task['s']
    rows=[];start=time.perf_counter()
    for i,(seed,zi) in enumerate(zip(seeds,z)):
        for arch in 'AD':
            out=simulate(int(seed),arch,zi,model={'steering_gain':task['g'],'dt':task['dt']})
            # Retain sufficient outcomes, identities and event diagnostics; full trajectory not logged.
            row={k:out[k] for k in ['scenario_seed','noise_seed','architecture','field_id','travel_direction','cards','mission_success','failure_code','duration','parking_attempted','parking_success','saturation_events','color_confusion_events','false_course_events']}
            row.update(bank_index=i,form=task['form'],s=task['s'],dt=task['dt'],g=task['g'])
            rows.append(row)
    pd.DataFrame(rows).to_csv(dest,index=False,compression='gzip')
    return f'{key}: {len(rows)} missions, {time.perf_counter()-start:.1f} s'
def run(tasks,workers=4):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for fut in as_completed([pool.submit(cell,t) for t in tasks]):print(fut.result(),flush=True)
def paired(task):
    x=pd.read_csv(R/'data/new'/f"{task['id']}.csv.gz")
    a=x[x.architecture=='A'].sort_values('bank_index');d=x[x.architecture=='D'].sort_values('bank_index')
    for col in ['scenario_seed','noise_seed','field_id','cards','travel_direction']:
        assert a[col].tolist()==d[col].tolist()
    assert len(a)==task['n'] and len(d)==task['n']
    assert not a.scenario_seed.duplicated().any()
    assert (x.mission_success==(x.failure_code=='SUCCESS')).all()
    return 1-a.mission_success.to_numpy(),1-d.mission_success.to_numpy()
def summarize(tasks,K,alpha):
    return pd.DataFrame([{**t,**simultaneous(*paired(t),K,alpha)} for t in tasks])
def prepare():
    for d in ['code/models','data/new','results','protocol','figures','source','evidence']:(R/d).mkdir(parents=True,exist_ok=True)
    source=R.parent/'IRIS_Starlight_Research/code/simulator/src'
    if not (R/'code/models/base').exists():shutil.copytree(source,R/'code/models/base',ignore=shutil.ignore_patterns('__pycache__'))
    for form in ['nonlinear','fractional','clearance']:
        if (R/'code/models'/form).exists():continue
        shutil.copytree(R/'code/models/base',R/'code/models'/form,ignore=shutil.ignore_patterns('__pycache__'))
        if form=='nonlinear':
            p=R/'code/models'/form/'actuator.py';s=p.read_text();old='target=(75.-clipped)*gain*np.pi/180.+z[6]*7*np.pi/180.'
            new='q=(75.-clipped)*np.pi/180.\n    target=gain*q*(1.-.15*(q/(60.*np.pi/180.))**2)+z[6]*7*np.pi/180.'
            assert old in s;p.write_text(s.replace(old,new))
        elif form=='fractional':
            p=R/'code/models'/form/'mission.py';s=p.read_text();old='''        delayed=buffer[(i-delay)%64] if i>=delay else 0.
        delayedv=vbuffer[(i-delay)%64] if i>=delay else 0.'''
            new='''        lagsteps=latency/dt
        lagfloor=int(np.floor(lagsteps));weight=lagsteps-lagfloor
        recent=buffer[(i-lagfloor)%64] if i>=lagfloor else 0.
        older=buffer[(i-lagfloor-1)%64] if i>=lagfloor+1 else 0.
        delayed=(1.-weight)*recent+weight*older
        recentv=vbuffer[(i-lagfloor)%64] if i>=lagfloor else 0.
        olderv=vbuffer[(i-lagfloor-1)%64] if i>=lagfloor+1 else 0.
        delayedv=(1.-weight)*recentv+weight*olderv'''
            assert old in s;p.write_text(s.replace(old,new))
        else:
            # Conservative decision envelope only: no change to pursuit or planned parking geometry.
            p=R/'code/models'/form/'vehicle.py';s=p.read_text().replace('a=length*.5;b=.064','a=length*.5+.005;b=.069').replace('rx=.5*length*abs(c)+.064*abs(s)','rx=(.5*length+.005)*abs(c)+.069*abs(s)').replace('ry=.5*length*abs(s)+.064*abs(c)','ry=(.5*length+.005)*abs(s)+.069*abs(c)');p.write_text(s)
            p=R/'code/models'/form/'mission.py';s=p.read_text().replace('slice_half=min(.5*length/','slice_half=min((.5*length+.005)/').replace('.064/max(1e-12,abs(np.cos(relative)))','.069/max(1e-12,abs(np.cos(relative)))').replace('rx=.5*length*abs(c)+.064*abs(sn)','rx=(.5*length+.005)*abs(c)+.069*abs(sn)').replace('ry=.5*length*abs(sn)+.064*abs(c)','ry=(.5*length+.005)*abs(sn)+.069*abs(c)');p.write_text(s)
    tasks=[]
    for g in np.round(np.linspace(1.2,1.3,11),3):
        for s in [.015,.03,.05]:
            for dt in [.01,.04]:tasks.append(dict(id=f'grid_g{g:.3f}_s{s:.3f}_dt{dt:.3f}',form='base',g=float(g),s=s,dt=dt,master=202610031,n=4000,family='grid'))
    for form in ['nonlinear','fractional','triangular','clearance']:
        for g in [1.2,1.25,1.3]:tasks.append(dict(id=f'form_{form}_g{g:.3f}',form=form,g=g,s=.03,dt=.04,master=202610031,n=4000,family='form'))
    protocol=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose='Finite declared-set ranking certificates; no physical validation',alpha_allocation={'grid':.02,'forms':.01,'confirmation':.01,'cartpole':.01},grid_K=66,form_K=15,confirmation_max_K=8,confirmation_N=8000,confirmation_master=202610032,cartpole_master=202610033,cartpole_N=2000,cartpole_grid={'gravity':[8.,9.8,12.],'half_length':[.35,.5,.65],'pole_mass':[.05,.1,.2]},cartpole_controllers={'A':'angle PD sign(10 theta + 2 theta_dot)','D':'nominal continuous LQR Q=diag(1,1,10,1), R=1; bang-bang sign(-K state)'},negative_controls='Identical A/A; global label swap; random within-pair swaps, 1000 repetitions; independent nominal banks; model-source invariance at zero compression; exact coverage enumeration',selection='After fixed grid: nominal, grid maximum, grid minimum, nearest negative point by normalized Euclidean distance; plus four nominal-line gain midpoints chosen first from opposite-sign adjacent estimates, then smallest endpoint absolute effect. Deduplicate, maximum 8. New confirmation bank only. No monotonicity assumption.',stopping='All fixed tasks run; no significance stopping. Failed missions retained.',grid_support='Declared engineering perturbations, not physically calibrated admissibility',tasks=tasks)
    proto=R/'protocol/frozen_protocol.json'
    if proto.exists():raise RuntimeError('Protocol exists; use run or confirm without re-freezing')
    proto.write_text(json.dumps(protocol,indent=2))
    sources={str(p.relative_to(R)):sha(p) for p in (R/'code').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    sources[str(proto.relative_to(R))]=sha(proto)
    (R/'protocol/freeze_hashes.json').write_text(json.dumps(sources,indent=2))
    print('Protocol frozen:',sha(proto),'missions:',sum(2*t['n'] for t in tasks),flush=True)
def verify_frozen():
    frozen=json.loads((R/'protocol/freeze_hashes.json').read_text())
    assert all(sha(R/p)==h for p,h in frozen.items()),'Frozen source changed'
def execute():
    verify_frozen();p=json.loads((R/'protocol/frozen_protocol.json').read_text());tasks=p['tasks'];run(tasks)
    grid=summarize(tasks[:66],66,.02);grid.to_csv(R/'results/grid.csv',index=False)
    base=[t for t in tasks[:66] if t['s']==.03 and t['dt']==.04 and t['g'] in [1.2,1.25,1.3]]
    forms=summarize(base+tasks[66:],15,.01);forms.to_csv(R/'results/forms.csv',index=False)
    print('GRID:',grid.groupby('region').size().to_dict(),flush=True);print('FORMS:',forms[['form','g','delta','lower','upper']].to_string(index=False),flush=True)
def confirm():
    verify_frozen();p=json.loads((R/'protocol/frozen_protocol.json').read_text());grid=pd.read_csv(R/'results/grid.csv')
    nominal=grid[(grid.g==1.2)&(grid.s==.03)&(grid.dt==.04)].iloc[0]
    selected=[dict(nominal),dict(grid.loc[grid.delta.idxmax()]),dict(grid.loc[grid.delta.idxmin()])]
    neg=grid[grid.delta<0].copy();neg['distance']=np.sqrt(((neg.g-1.2)/.1)**2+((neg.s-.03)/.035)**2+((neg.dt-.04)/.03)**2)
    if len(neg):selected.append(dict(neg.sort_values(['distance','g','s','dt']).iloc[0]))
    line=grid[(grid.s==.03)&(grid.dt==.04)].sort_values('g');intervals=[]
    for i in range(len(line)-1):
        a=line.iloc[i];b=line.iloc[i+1];intervals.append((0 if a.delta*b.delta<0 else 1,min(abs(a.delta),abs(b.delta)),float((a.g+b.g)/2)))
    for _,__,g in sorted(intervals)[:4]:selected.append(dict(form='base',g=round(g,4),s=.03,dt=.04))
    tasks=[];seen=set()
    for t in selected:
        key=(t['g'],t['s'],t['dt'])
        if key in seen:continue
        seen.add(key);tasks.append(dict(id=f'confirm_g{key[0]:.4f}_s{key[1]:.3f}_dt{key[2]:.3f}',form='base',g=key[0],s=key[1],dt=key[2],master=p['confirmation_master'],n=p['confirmation_N'],family='confirmation'))
    fn=R/'protocol/confirmation_selection.json'
    if fn.exists():assert json.loads(fn.read_text())['tasks']==tasks
    else:fn.write_text(json.dumps(dict(selected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),grid_sha256=sha(R/'results/grid.csv'),tasks=tasks),indent=2))
    run(tasks);out=summarize(tasks,8,.01);out.to_csv(R/'results/confirmation.csv',index=False)
    print('CONFIRMATION:',out[['g','s','dt','delta','lower','upper','region']].to_string(index=False),flush=True)
if __name__=='__main__':
    mode=sys.argv[1]
    {'prepare':prepare,'run':execute,'confirm':confirm}[mode]()
