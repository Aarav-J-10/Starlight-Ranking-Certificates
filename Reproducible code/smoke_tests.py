"""Regression and analytical-oracle sanity tests for the reproducible synthetic study."""
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
root=Path(__file__).parent
spec=importlib.util.spec_from_file_location('study',root/'run_benchmark.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rng=np.random.default_rng(20261123)
for name,setting in [('baseline',[1.20,.035,.04]),('heavy_tail',[1.26,.050,.04]),
                     ('exact_tie',[1.24,.035,.01]),('small_effect',[1.27,.035,.04])]:
    A,D,ya,yd=m.simulate_one(rng,setting,180000,name)
    truth=m.oracle_delta(*setting,name)
    obs=(yd-ya).mean()
    se=(yd-ya).std(ddof=1)/np.sqrt(len(ya))
    assert abs(obs-truth)<4*se,(name,obs,truth,se)
assert abs(m.oracle_delta(1.24,.035,.01,'exact_tie'))<1e-14
l,u=m.cp_interval(0,0,700,k=54)
assert l<0<u
# audit expected rows and deterministic primary benchmark outcomes
r=pd.read_csv(root/'final'/'all_decisions.csv')
assert len(r)==6*54*100*7
assert set(r.method)=={'Starlight CP + Bonferroni','CNN (1D error histogram)',
  'PINN (physics-informed response)','Random forest + abstention','Logistic regression',
  'Random forest','Raw failure difference'}
assert ((r.outcome=='correct')|(r.outcome=='unsupported')|(r.outcome=='abstain')).all()
print('PASS: four oracle Monte Carlo checks, null/CP checks, 226800 recorded decision rows, seven methods')
