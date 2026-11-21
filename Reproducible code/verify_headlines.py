#!/usr/bin/env python3
"""Recalculate headline numbers from final/summary.csv. Run from package root or anywhere."""
from pathlib import Path
import pandas as pd
root=Path(__file__).resolve().parents[1]
df=pd.read_csv(root/'02_Complete_Results'/'summary.csv')
agg=df.groupby('method')[['correct','unsupported','abstain','n']].sum()
print(agg.to_string())
st=agg.loc['Starlight CP + Bonferroni']
assert int(st.unsupported)==0 and int(st.n)==32400 and int(st.abstain)==17651
assert set(df.regime)=={'baseline','nonlinear','heavy_tail','model_break','small_effect','exact_tie'}
assert (df.correct+df.unsupported+df.abstain==df.n).all()
print('\nChecks passed. Public claims must include abstentions and synthetic-model limitations.')
