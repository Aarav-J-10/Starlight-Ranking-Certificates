"""Public scalar Gymnasium executor, replacing an acceleration candidate that failed validation."""
from pathlib import Path
import json,datetime,hashlib,inspect,shutil
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
from experiment import R,verify_frozen,simultaneous
from cartpole import controllers
def cell(t):
    from gymnasium.envs.classic_control.cartpole import CartPoleEnv
    n=t['n'];states=np.random.default_rng(t['master']).uniform(-.05,.05,(n,4));gains=controllers();env=CartPoleEnv();env.reset(seed=t['master'])
    env.gravity=t['gravity'];env.length=t['half_length'];env.masspole=t['pole_mass'];env.total_mass=1.+env.masspole;env.polemass_length=env.masspole*env.length
    rows=[];failure=[]
    for arch in 'AD':
        ff=[]
        for i,state in enumerate(states):
            env.state=state.copy();env.steps_beyond_terminated=None;obs=state.astype(np.float32);failed=0
            for k in range(500):
                action=int(gains[arch]@obs>=0);obs,_,term,_,_=env.step(action)
                if term:failed=1;break
            ff.append(failed);rows.append(dict(specification=t['id'],bank_index=i,controller=arch,failed=failed,steps=k+1,gravity=t['gravity'],half_length=t['half_length'],pole_mass=t['pole_mass']))
        failure.append(np.array(ff))
    env.close();pd.DataFrame(rows).to_csv(R/'data/new'/f"cartpole_{t['id']:02}.csv.gz",index=False,compression='gzip')
    return dict(**t,**simultaneous(*failure,27,.01))
def main():
    import gymnasium,itertools
    from gymnasium.envs.classic_control.cartpole import CartPoleEnv
    verify_frozen();assert gymnasium.__version__=='1.2.1'
    p=json.loads((R/'protocol/frozen_protocol.json').read_text());g=p['cartpole_grid']
    tasks=[dict(id=i,gravity=a,half_length=b,pole_mass=c,n=p['cartpole_N'],master=p['cartpole_master']) for i,(a,b,c) in enumerate(itertools.product(g['gravity'],g['half_length'],g['pole_mass']))]
    here=Path(__file__)
    amendment=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='Accelerated candidate failed full closed-loop state equivalence against Gymnasium (max state discrepancy 0.007836 at one tested endpoint). Candidate outputs are not evidence. Production now executes the public scalar environment directly.',unchanged='Controllers, physics grid, initial states, sample size, stopping, alpha allocation and success definition unchanged; no complete benchmark table observed before amendment.',executor_sha256=hashlib.sha256(here.read_bytes()).hexdigest(),tasks=tasks)
    fn=R/'protocol/cartpole_executor_amendment.json'
    if fn.exists():assert json.loads(fn.read_text())['executor_sha256']==amendment['executor_sha256']
    else:fn.write_text(json.dumps(amendment,indent=2))
    src=Path(inspect.getfile(CartPoleEnv));shutil.copy2(src,R/'evidence/gymnasium_1_2_1_cartpole.py')
    results=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(cell,t) for t in tasks]):
            r=f.result();results.append(r);print('Public CartPole',len(results),'/27',r['delta'],r['region'],flush=True)
    pd.DataFrame(results).sort_values('id').to_csv(R/'results/cartpole.csv',index=False)
    m=R/'results/cartpole_metadata.json';meta=json.loads(m.read_text());meta['executor']='Unmodified Gymnasium 1.2.1 CartPoleEnv.step; fixed physics overrides and 500-step horizon';meta['accelerated_candidate']='Rejected; not used for production results';m.write_text(json.dumps(meta,indent=2))
if __name__=='__main__':main()
