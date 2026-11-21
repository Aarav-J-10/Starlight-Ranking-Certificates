from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1]
out=[]
def table(d,title,subtitle,detail=True):
    out.append(r'\pageheading{SUPPLEMENTARY INFORMATION}{'+title+'}\n'+subtitle+'\n')
    out.append(r'\par\begingroup\scriptsize\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.15}'+'\n')
    out.append(r'\begin{tabularx}{\linewidth}{@{}rrrrrrYc@{}}\toprule'+'\n')
    out.append(r'$g$ & $s$ & $\Delta t$ & $n_+$ & $n_-$ & $\widehat\Delta$ (pp) & Simultaneous interval (pp) & Sign\\\midrule'+'\n')
    for _,r in d.iterrows():
        out.append(f"{r.g:.3f} & {r.s:.3f} & {r['dt']:.2f} & {int(r.plus)} & {int(r.minus)} & {100*r.delta:+.3f} & [{100*r.lower:+.3f}, {100*r.upper:+.3f}] & {r.region} \\\\\n")
    out.append(r'\bottomrule\end{tabularx}\endgroup'+'\n')
    out.append(r'\par\vspace{3mm}$n_+$ counts D-only failures; $n_-$ counts A-only failures. A means the interval is strictly positive, D strictly negative, and U unresolved. Positive differences favor A.'+'\n')
g=pd.read_csv(R/'results/grid.csv')
for i,(dt,d) in enumerate(g.groupby('dt')):table(d,f'S{6+i} / Complete primary grid: {dt:.2f} s',r'All cells use $N=4000$, $K=66$, and family error budget $\alpha=0.02$.')
table(pd.read_csv(R/'results/confirmation.csv'),'S8 / Independent confirmation counts',r'All cells use $N=8000$, $K=8$, and family error budget $\alpha=0.01$. Selection preceded the independent outcomes.')
out.append(r'\head{Verification and coverage enumeration}'+'\n')
coverage=pd.read_csv(R/'results/coverage_enumeration.csv')
out.append(r'\par{\tbl\begin{tabularx}{\linewidth}{@{}rrY@{}}\toprule $p_+$ & $p_-$ & Exact enumerated coverage ($N=30$, nominal 95\%)\\\midrule'+'\n')
for _,r in coverage.iterrows():out.append(f'{r.p_plus:.3f} & {r.p_minus:.3f} & {100*r.coverage:.4f}\\% \\\\\n')
out.append(r'\bottomrule\end{tabularx}}'+'\n')
out.append(r'\par The machine-readable tables additionally provide marginal failure rates, Hoeffding bounds, all fifteen form comparisons, twenty-seven CartPole comparisons, the retrospective thirty-two-cell audit, and descriptive paired contrasts. Every new production outcome is included in compressed row-level files.'+'\n')
(R/'source/supplement_tables.tex').write_text(''.join(out),encoding='utf-8')
