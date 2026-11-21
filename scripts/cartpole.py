"""External computational case: Gymnasium 1.2.1 CartPole, perturbed physics.
The accelerated dynamics are checked against the installed public environment.
"""
from pathlib import Path
import sys,json,hashlib,shutil,inspect,itertools,math
import numpy as np
import pandas as pd
from numba import njit
from scipy.linalg import solve_continuous_are
from experiment import R,simultaneous,verify_frozen
@njit(cache=True)
def derivative(state,force,gravity,length,masspole):
    x,xd,theta,td=state
    total=1.+masspole;pm=masspole*length;c=math.cos(theta);sn=math.sin(theta)
    temp=(force+pm*td*td*sn)/total
    tacc=(gravity*sn-c*temp)/(length*(4./3.-masspole*c*c/total))
    xacc=temp-pm*tacc*c/total
    return np.array([xd,xacc,td,tacc])
@njit(cache=True)
def action(state,gain):
    val=0.
    for j in range(4):val+=gain[j]*float(np.float32(state[j]))
    return 1 if val>=0 else 0
@njit(cache=True)
def episode(initial,gain,gravity,length,masspole):
    state=initial.copy()
    for k in range(500):
        a=action(state,gain);force=10. if a else -10.
        state=state+.02*derivative(state,force,gravity,length,masspole)
        if abs(state[0])>2.4 or abs(state[2])>12*2*math.pi/360:
            return 1,k+1,state
    return 0,500,state
def controllers():
    # Linearization of the nominal source equations, using an outcome-free derivative calculation.
    state=np.zeros(4);eps=1e-6
    A=np.column_stack([(derivative(state+np.eye(4)[j]*eps,0,9.8,.5,.1)-derivative(state-np.eye(4)[j]*eps,0,9.8,.5,.1))/(2*eps) for j in range(4)])
    B=((derivative(state,eps,9.8,.5,.1)-derivative(state,-eps,9.8,.5,.1))/(2*eps))[:,None]
    Q=np.diag([1.,1.,10.,1.]);P=solve_continuous_are(A,B,Q,np.ones((1,1)))
    gain=-(B.T@P).ravel()
    return {'A':np.array([0.,0.,10.,2.]),'D':gain}
def main():
    verify_frozen()
    import gymnasium
    from gymnasium.envs.classic_control.cartpole import CartPoleEnv
    assert gymnasium.__version__=='1.2.1'
    p=json.loads((R/'protocol/frozen_protocol.json').read_text());n=p['cartpole_N'];master=p['cartpole_master']
    states=np.random.default_rng(master).uniform(-.05,.05,(n,4));gains=controllers();pd.DataFrame(states,columns=['x','x_dot','theta','theta_dot']).to_csv(R/'data/cartpole_initial_states.csv',index=False)
    src=Path(inspect.getfile(CartPoleEnv));shutil.copy2(src,R/'evidence/gymnasium_1_2_1_cartpole.py')
    meta=dict(gymnasium_version=gymnasium.__version__,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),source_url='https://github.com/Farama-Foundation/Gymnasium/blob/v1.2.1/gymnasium/envs/classic_control/cartpole.py',controller_gains={k:v.tolist() for k,v in gains.items()},observation='float32, matching public observation API',success='No termination during 500 steps; time-limit truncation is success',modified_parameters=p['cartpole_grid'])
    (R/'results/cartpole_metadata.json').write_text(json.dumps(meta,indent=2))
    values=p['cartpole_grid'];specs=list(itertools.product(values['gravity'],values['half_length'],values['pole_mass']))
    results=[];raw=[];verify=[]
    for index,(gravity,length,masspole) in enumerate(specs):
        failures=[]
        for arch in 'AD':
            ff=[]
            for i,state in enumerate(states):
                failed,steps,last=episode(state,gains[arch],gravity,length,masspole);ff.append(failed)
                raw.append(dict(specification=index,bank_index=i,controller=arch,gravity=gravity,half_length=length,pole_mass=masspole,failed=failed,steps=steps))
            failures.append(np.array(ff))
            # Two complete held-out trajectories per cell/controller against public Python implementation.
            for i in [0,n-1]:
                env=CartPoleEnv();env.reset(seed=master+i);env.gravity=gravity;env.length=length;env.masspole=masspole;env.total_mass=1.+masspole;env.polemass_length=masspole*length;env.state=states[i].copy()
                fail=0
                for k in range(500):
                    a=action(np.array(env.state),gains[arch]);_,_,terminated,_,_=env.step(a)
                    if terminated:fail=1;break
                expected,steps,last=episode(states[i],gains[arch],gravity,length,masspole)
                error=float(np.max(np.abs(np.array(env.state)-last)))
                assert fail==expected and k+1==steps and error<1e-10,(index,arch,i,error)
                verify.append(dict(specification=index,controller=arch,bank_index=i,steps=steps,matched=True,max_state_error=error))
                env.close()
        result=dict(specification=index,gravity=gravity,half_length=length,pole_mass=masspole,**simultaneous(*failures,27,.01));results.append(result)
        print('CartPole',index+1,'/27',result['delta'],result['region'],flush=True)
    pd.DataFrame(raw).to_csv(R/'data/cartpole_trials.csv.gz',index=False,compression='gzip');pd.DataFrame(results).to_csv(R/'results/cartpole.csv',index=False);pd.DataFrame(verify).to_csv(R/'results/cartpole_equivalence.csv',index=False)
if __name__=='__main__':main()
