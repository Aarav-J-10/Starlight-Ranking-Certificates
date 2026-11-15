#!/usr/bin/env python3
"""Regenerate fair-ready figures from UNMODIFIED published processed CSVs.

Read-only: it neither creates study observations nor changes the reference tables.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'REFERENCE_DATA/starlight-iris-2026'
DEST = ROOT / 'docs/figures'
DEST.mkdir(parents=True, exist_ok=True)
INK = '#11243b'
NAVY = '#21589b'
TEAL = '#078c86'
AMBER = '#c88b25'
RED = '#d35f55'
LIGHT = '#e4eaf2'
TEXT = '#33465e'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.titlesize': 18, 'axes.titleweight': 'bold',
    'axes.labelsize': 11, 'text.color': INK,
    'axes.labelcolor': TEXT, 'xtick.color': TEXT, 'ytick.color': TEXT,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'savefig.facecolor': 'white', 'savefig.dpi': 185,
})

def finish(fig, name):
    fig.savefig(DEST / name, dpi=185, bbox_inches='tight', pad_inches=.22)
    plt.close(fig)

def foot(fig, s):
    fig.text(.06,.035,s,fontsize=9,color='#53657c',va='bottom')

# 1. Certified witness intervals: exactly the two archived rows that agree with the fresh CP audit.
cf = pd.read_csv(DATA/'simulation/confirmation.csv')
w = cf[(cf.stress_s == .03) & (cf.timestep_s == .04) & (cf.gain_g.isin([1.2,1.26]))].sort_values('gain_g')
assert len(w) == 2
assert list(np.round(w.delta_pp.values, 3)) == [1.050, -2.925]
fig,ax=plt.subplots(figsize=(9.6,4.8))
fig.subplots_adjust(left=.18,right=.96,top=.77,bottom=.27)
ax.axvline(0,color=TEXT,lw=1.15,linestyle='--')
for i, row in enumerate(w.itertuples()):
    low, mid, high = row.ci_low_pp, row.delta_pp, row.ci_high_pp
    color = NAVY if mid>0 else TEAL
    ax.plot([low,high],[i,i], lw=5,color=color,solid_capstyle='round')
    ax.plot([low,low],[i-.11,i+.11], lw=2,color=color)
    ax.plot([high,high],[i-.11,i+.11], lw=2,color=color)
    ax.scatter(mid,i,s=125,color=color,zorder=4,edgecolor='white',linewidth=1.8)
    ax.text(mid, i+.19, f'{mid:+.3f} pp', color=color, weight='bold',ha='center',fontsize=13)
ax.set_yticks([0,1],['g = 1.200\nA favored','g = 1.260\nD favored'])
ax.invert_yaxis()
ax.set_xlim(-5,3)
ax.set_ylim(1.65,-.65)
ax.grid(axis='x',alpha=.15)
ax.set_xlabel('Paired simulated failure-risk difference: D minus A (percentage points)')
fig.suptitle('A small gain change reverses the supported ranking', x=.06,ha='left',y=.97,fontsize=18,fontweight='bold')
fig.text(.06,.84,'Independent confirmation · same stress s = 0.030 and time step dt = 0.040 s',fontsize=11,color=TEXT)
foot(fig,'Dots: estimated differences; lines: archived confirmation simultaneous intervals. Two selected witnesses, not a physical car comparison.')
finish(fig,'01_confirmed_reversal.png')

# 2. primary grid certificate counts
pg=pd.read_csv(DATA/'simulation/primary_grid.csv')
counts=pg.certificate_label.value_counts().to_dict()
assert (counts['A'],counts['D'],counts['unresolved'])==(8,29,29)
fig,ax=plt.subplots(figsize=(9.6,3.35));fig.subplots_adjust(left=.06,right=.96,bottom=.26,top=.78)
left=0
for name,count,color in [('A favored',8,NAVY),('D favored',29,TEAL),('Unresolved',29,AMBER)]:
    ax.barh(0,count,left=left,height=.55,color=color)
    ax.text(left+count/2,0,f'{count}',ha='center',va='center',color='white',weight='bold',fontsize=20)
    left+=count
ax.set(xlim=(0,66),ylim=(-.5,.5));ax.axis('off')
fig.suptitle('One 66-condition family. No universal winner.',x=.06,ha='left',y=.98,fontsize=18,fontweight='bold')
fig.legend(handles=[Patch(color=NAVY,label='A favored · 8'),Patch(color=TEAL,label='D favored · 29'),Patch(color=AMBER,label='Unresolved · 29')],loc='lower left',bbox_to_anchor=(.05,.12),ncol=3,frameon=False)
foot(fig,'Per-condition labels are from the published processed primary-grid file; unresolved does not mean equivalent.')
finish(fig,'02_grid_certificates.png')

# 3. physical descriptive cohorts. Keep matched and mismatch labels distinct.
wp4=pd.read_csv(DATA/'physical/wp4/clock_compass_pairs.csv')
cohorts=[('dial_pilot','mismatch','Dial pilot\nmismatch'),('linkage_consolidated','mismatch','Linkage\nmismatch'),('linkage_consolidated','matched','Linkage\nmatched')]
clock=[];compass=[]
for session,condition,_ in cohorts:
    rows=wp4[(wp4.session==session)&(wp4.condition==condition)]
    clock.append(rows[rows.controller=='Clock'].heading_shift_deg.mean())
    compass.append(rows[rows.controller=='Compass'].heading_shift_deg.mean())
assert np.allclose(clock,[6.80,6.42,6.64]); assert np.allclose(compass,[1.10,.48,.65])
fig,ax=plt.subplots(figsize=(9.6,5.0));fig.subplots_adjust(left=.12,right=.97,bottom=.28,top=.77)
x=np.arange(3);width=.32
bars1=ax.bar(x-width/2,clock,width,color=NAVY,label='Clock')
bars2=ax.bar(x+width/2,compass,width,color=TEAL,label='Compass')
for bars in [bars1,bars2]:
    for b in bars: ax.text(b.get_x()+b.get_width()/2,b.get_height()+.12,f'{b.get_height():.2f}°',ha='center',fontsize=11,weight='bold')
ax.set_xticks(x,[z[2] for z in cohorts]);ax.set_ylabel('Recorded heading-shift magnitude (degrees)')
ax.set_ylim(0,8.1);ax.grid(axis='y',alpha=.18)
ax.legend(loc='upper right',frameon=False,ncol=2)
fig.suptitle('Physical docking: heading response by cohort',x=.06,ha='left',y=.97,fontsize=18,fontweight='bold')
fig.text(.06,.85,'Clock = preset turns   ·   Compass = heading feedback',fontsize=11,color=TEXT)
foot(fig,'Descriptive means only. Cohorts have distinct n; matched Clock mean (6.64°) exceeds mismatch mean (6.42°). No causal contrast.')
finish(fig,'03_physical_heading_cohorts.png')

# 4. accuracy test with separate units shown clearly.
cam=pd.read_csv(DATA/'physical/wp3/dock_camera_accuracy.csv')
position=np.percentile(cam.position_error_mm,95)
heading=np.percentile(cam.heading_error_deg,95)
assert abs(position-2.480)<.01 and abs(heading-1.286)<.01
fig,axes=plt.subplots(1,2,figsize=(9.6,4.4));fig.subplots_adjust(left=.08,right=.97,bottom=.23,top=.72,wspace=.29)
for ax,observed,target,unit,label,col in zip(axes,[position,heading],[2.5,1.0],['mm','degrees'],['Position · PASS','Heading · FAIL'],[TEAL,RED]):
    ax.barh([0],[observed],color=col,height=.4)
    ax.axvline(target,color=INK,linestyle='--',linewidth=2,label=f'Target {target:.1f} {unit}')
    ax.text(observed+.02*max(target,observed),0,f'{observed:.3f} {unit}',va='center',fontsize=12,weight='bold',color=col)
    ax.set(xlim=(0,max(observed,target)*1.37),yticks=[],xlabel=f'95th percentile error ({unit})')
    ax.set_title(label,fontsize=14,color=col)
    ax.legend(frameon=False,loc='lower right',fontsize=9)
fig.suptitle('Camera metrology: position passes, heading misses',x=.06,ha='left',y=.97,fontsize=17,fontweight='bold')
fig.text(.06,.83,f'{len(cam)} camera frames · sample 95th percentiles; dashed line = acceptance target',fontsize=11,color=TEXT)
foot(fig,'Source: WP3 processed frame-error CSV. A failed engineering requirement is reported, not hidden.')
finish(fig,'04_camera_accuracy_limits.png')

# 5. sorter pooled recipe accuracy, not inferential independence.
cs=pd.read_csv(DATA/'physical/wp8/colour_sorter.csv')
g=cs.groupby('recipe',sort=False)[['n_items','n_correct']].sum()
labels=['S1_fixed','S2_calibrated','S3_recheck']; acc=[100*g.loc[k,'n_correct']/g.loc[k,'n_items'] for k in labels]
fig,ax=plt.subplots(figsize=(9.6,4.5));fig.subplots_adjust(left=.11,right=.96,bottom=.29,top=.77)
bars=ax.bar(range(3),acc,color=[AMBER,TEAL,NAVY],width=.56)
for i,k in enumerate(labels): ax.text(i,acc[i]+2,f"{g.loc[k,'n_correct']}/{g.loc[k,'n_items']}  ·  {acc[i]:.1f}%",ha='center',fontsize=10.5,weight='bold')
ax.set_xticks(range(3),['S1 · fixed threshold','S2 · calibrated','S3 · rechecking'])
ax.set_ylim(0,109);ax.set_ylabel('Correct items / pooled items (%)');ax.grid(axis='y',alpha=.16)
fig.suptitle('Transfer test: three colour-sorting recipes',x=.06,ha='left',y=.97,fontsize=18,fontweight='bold')
fig.text(.06,.85,'Accuracy from 34 reported batches, aggregated by recipe',fontsize=11,color=TEXT)
foot(fig,'Items within a batch may be dependent. Bars describe pooled recorded outcomes, not an independent-item confidence claim.')
finish(fig,'05_sorter_transfer.png')

# 6. physical docking session totals
sess=pd.read_csv(DATA/'physical/wp5_wp6/docking_session_summary.csv')
assert sess.clock_success.sum()==41 and sess.compass_success.sum()==53
fig,ax=plt.subplots(figsize=(9.6,4.8));fig.subplots_adjust(left=.10,right=.97,bottom=.24,top=.78)
x=np.arange(len(sess));w=.35
ax.bar(x-w/2,sess.clock_success,w,label='Clock',color=NAVY)
ax.bar(x+w/2,sess.compass_success,w,label='Compass',color=TEAL)
ax.set_xticks(x,sess.session);ax.set_ylim(0,13);ax.set_yticks([0,3,6,9,12]);ax.set_ylabel('Docking successes / 12 scenarios');ax.grid(axis='y',alpha=.15)
ax.legend(frameon=False,ncol=2,loc='upper right')
fig.suptitle('Docking: five paired sessions, aggregate outcomes',x=.06,ha='left',y=.97,fontsize=18,fontweight='bold')
fig.text(.06,.85,'Clock: 41/60 successes · Compass: 53/60 successes',fontsize=11,color=TEXT)
foot(fig,'Session-level marginals do not recover which individual paired runs were discordant.')
finish(fig,'06_docking_session_totals.png')
print(f'Generated {len(list(DEST.glob("*.png")))} figures from unchanged processed CSVs.')
