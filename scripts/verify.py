"""Recheck hashes, retained counts, and the frozen zero-compression control."""
from pathlib import Path
import json,sys,hashlib,shutil,importlib
import pandas as pd
import numpy as np
from experiment import R,verify_frozen,paired,summarize,bank
def main():
    verify_frozen();p=json.loads((R/'protocol/frozen_protocol.json').read_text());c=json.loads((R/'protocol/confirmation_selection.json').read_text())
    assert hashlib.sha256((R/'results/grid.csv').read_bytes()).hexdigest()==c['grid_sha256']
    amend=json.loads((R/'protocol/cartpole_executor_amendment.json').read_text())
    assert hashlib.sha256((R/'code/cartpole_public.py').read_bytes()).hexdigest()==amend['executor_sha256']
    tasks=p['tasks']+c['tasks'];missions=0
    for t in tasks:
        paired(t);missions+=2*t['n']
    ext=pd.read_csv(R/'results/cartpole.csv');external=0
    for _,row in ext.iterrows():
        d=pd.read_csv(R/'data/new'/f'cartpole_{int(row.id):02}.csv.gz');assert len(d)==4000
        a=d[d.controller=='A'].sort_values('bank_index');b=d[d.controller=='D'].sort_values('bank_index');assert a.bank_index.tolist()==b.bank_index.tolist();assert abs((b.failed.to_numpy()-a.failed.to_numpy()).mean()-row.delta)<1e-14;external+=len(d)
    # Create a separate control module; never alter any frozen model source.
    dest=R/'code/control_zero';shutil.copytree(R/'code/models/nonlinear',dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    fn=dest/'actuator.py';source=fn.read_text();assert '.15*' in source;fn.write_text(source.replace('.15*','0.*'))
    sys.path.insert(0,str(R/'code'));sys.path.insert(0,str(R/'code/models'))
    from base.mission import simulate as base
    from control_zero.mission import simulate as zero
    seeds,u,w=bank(202610036,20);z=u.copy();z[:,[2,3,6]]=2*z[:,[2,3,6]]-1;z*=.03;checks=[]
    for seed,zi in zip(seeds,z):
        for arch in 'AD':
            x=base(int(seed),arch,zi);y=zero(int(seed),arch,zi)
            keys=['failure_code','duration','mission_success','saturation_events','parking_success']
            checks.append(all(x[k]==y[k] for k in keys))
    assert all(checks)
    report=dict(frozen_hashes_verified=True,confirmation_selection_grid_hash_verified=True,public_executor_hash_verified=True,robot_missions=missions,cartpole_episodes=external,total_production=missions+external,zero_compression_pairs=len(checks),zero_compression_exact=all(checks),zero_compression_master=202610036,extra_control_executions=2*len(checks)+40)
    (R/'results/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
