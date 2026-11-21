"""Publication figures generated only from retained outcomes."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
BG='#070A0F';INK='#F2ECE6';A='#9FBEEC';D='#E8AE88';U='#929CA9'
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'savefig.facecolor':BG,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'axes.edgecolor':'#657489','font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
def save(fig,name):
    fig.savefig(R/'figures'/f'{name}.pdf',bbox_inches='tight');fig.savefig(R/'figures'/f'{name}.png',dpi=150,bbox_inches='tight');plt.close(fig)
def forest(ax,d,labels):
    for i,(_,r) in enumerate(d.iterrows()):
        c=A if r.lower>0 else (D if r.upper<0 else U)
        ax.plot([100*r.lower,100*r.upper],[i,i],color=c,lw=1.6);ax.scatter(100*r.delta,i,color=c,s=23,zorder=3)
    ax.axvline(0,color=INK,lw=.8,alpha=.7);ax.set_yticks(range(len(d)),labels);ax.invert_yaxis();ax.set_xlabel('Failure-risk difference D − A (percentage points)');ax.grid(axis='x',alpha=.15)
def main():
    grid=pd.read_csv(R/'results/grid.csv');forms=pd.read_csv(R/'results/forms.csv');confirm=pd.read_csv(R/'results/confirmation.csv')
    fig,ax=plt.subplots(figsize=(9,4.3));p=pd.read_csv(R/'data/historical/physical_timing_records.csv')
    for i,(cohort,d) in enumerate(p.groupby('cohort',sort=False)):
        vals=d.time_seconds.to_numpy();ax.scatter(np.arange(len(vals))+1,vals,color=A if i==0 else D,label='Development (19 successes)' if i==0 else 'Practice (12 successes)',s=40)
        ax.plot(np.arange(len(vals))+1,vals,color=A if i==0 else D,alpha=.4)
    ax.set(xlabel='Order within retained cohort',ylabel='Completion time (s)',ylim=(15,40));ax.legend(frameon=False);ax.grid(alpha=.15);save(fig,'timing')
    fig,axs=plt.subplots(1,2,figsize=(10,7.5),sharex=True)
    for ax,(dt,d) in zip(axs,grid.groupby('dt')):
        d=d.sort_values(['g','s']);forest(ax,d,[f'{r.g:.2f} / {r.s:.3f}' for _,r in d.iterrows()]);ax.set_title(f'Time step {dt:.2f} s');ax.tick_params(axis='y',labelsize=8);ax.set_ylabel('Gain / stress')
    fig.tight_layout(w_pad=2);save(fig,'grid_forest')
    fig,ax=plt.subplots(figsize=(9,4.7))
    for (s,dt),d in grid.groupby(['s','dt']):
        ax.plot(d.g,100*d.delta,marker='o',ms=4,ls='-' if dt==.04 else '--',label=f's={s:.3f}, dt={dt:.2f}')
    ax.axhline(0,color=INK,lw=.8);ax.set(xlabel='Steering gain',ylabel='Failure-risk difference D − A (pp)');ax.legend(frameon=False,ncol=2,fontsize=9);ax.grid(alpha=.15);save(fig,'gain_curves')
    fig,ax=plt.subplots(figsize=(9,4.4));central=grid[(grid.s==.03)&(grid.dt==.04)];ax.plot(central.g,central.delta*100,'o-',color=U,label='Fixed search grid');ax.fill_between(central.g,central.lower*100,central.upper*100,color=U,alpha=.2)
    c=confirm[(confirm.s==.03)&(confirm.dt==.04)].sort_values('g');ax.errorbar(c.g,c.delta*100,yerr=np.array([c.delta-c.lower,c.upper-c.delta])*100,fmt='s',color=A,capsize=4,label='Independent confirmation');ax.axhline(0,color=INK,lw=.8);ax.set(xlabel='Steering gain (stress 0.030; time step 0.04 s)',ylabel='Failure-risk difference D − A (pp)');ax.legend(frameon=False,fontsize=10);ax.grid(alpha=.15);save(fig,'confirmation')
    fig,ax=plt.subplots(figsize=(9,5.9));forest(ax,forms,[f'{r.form:10s}  g={r.g:.2f}' for _,r in forms.iterrows()]);fig.tight_layout();save(fig,'forms')
    attr=pd.read_csv(R/'results/attribution.csv');fig,axs=plt.subplots(1,2,figsize=(10,4.4),gridspec_kw={'width_ratios':[1,1.35]});axs[0].barh(attr.component,attr.fraction*100,color=A);axs[0].invert_yaxis();axs[0].set_xlabel('Finite-grid variation (%)');axs[0].grid(axis='x',alpha=.15)
    con=pd.read_csv(R/'results/paired_attribution_contrasts.csv').rename(columns={'change':'delta','lo':'lower','hi':'upper'});forest(axs[1],con,[f"{r.s:.3f} / {r['dt']:.2f}" for _,r in con.iterrows()]);axs[1].set_xlabel('Gain 1.30 minus 1.20 effect change (pp)');axs[1].set_ylabel('Stress / time step');fig.tight_layout(w_pad=2);save(fig,'attribution')
    ctrl=pd.read_csv(R/'results/random_label_controls.csv');fig,ax=plt.subplots(figsize=(9,3.8));ax.hist(ctrl.delta*100,bins=25,color=A,edgecolor=BG);ax.axvline(0,color=INK,lw=1);ax.set(xlabel='Random-label paired difference (pp)',ylabel='Repetitions (of 1,000)');save(fig,'controls')
    ext=pd.read_csv(R/'results/cartpole.csv');fig,axs=plt.subplots(1,3,figsize=(10,5.4),sharex=True)
    for ax,(gravity,d) in zip(axs,ext.groupby('gravity')):
        forest(ax,d,[f'{r.half_length:.2f} / {r.pole_mass:.2f}' for _,r in d.iterrows()]);ax.set_title(f'Gravity {gravity:g} m/s²');ax.set_xlabel('Risk difference (pp)');ax.tick_params(axis='y',labelsize=9)
    axs[0].set_ylabel('Half-length (m) / pole mass (kg)');fig.tight_layout(w_pad=2);save(fig,'cartpole')
    fig,ax=plt.subplots(figsize=(10,3.5));ax.axis('off')
    boxes=[(.01,'DECLARE','Designs, loss, model family\nscenario law, error budget'),(.35,'ESTIMATE','Matched independent scenarios\nsimultaneous intervals'),(.69,'CERTIFY','Uniform A / Uniform D\nNon-robust / Unresolved')]
    for x,title,body in boxes:
        ax.text(x+.145,.72,title,ha='center',weight='bold',color=A,fontsize=13);ax.text(x+.145,.44,body,ha='center',va='center',fontsize=11,bbox=dict(facecolor='#141C29',edgecolor='#657489',boxstyle='round,pad=1'))
    ax.annotate('',xy=(.345,.44),xytext=(.30,.44),arrowprops=dict(arrowstyle='->',color=INK));ax.annotate('',xy=(.685,.44),xytext=(.64,.44),arrowprops=dict(arrowstyle='->',color=INK));ax.text(.5,.06,'Adaptive search → freeze candidates → independent confirmation bank',ha='center',color=D,fontsize=11);save(fig,'workflow')
if __name__=='__main__':main()
