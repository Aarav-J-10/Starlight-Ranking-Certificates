"""Official 2026 obstacle field, metres. Four 1m corridors around a 1m square.

Pillars occupy six official seats per straight (longitudinal 0,.5,1 and
distance .4/.6 from the inner wall). Card patterns loaded from the visual rule
transcription. Parking-section signs move to the inner row. Track tolerances
are omitted; this is a nominal-size valid field family, not Open Challenge.
All architectures receive the identical field for a scenario seed.
"""
import json
from pathlib import Path
import numpy as np
from numba import njit
SEGMENT=1+np.pi/4
PERIMETER=4*SEGMENT
CARDS=json.loads(Path(__file__).with_name('official_cards.json').read_text())

@njit(cache=True)
def path(s):
    s=s%PERIMETER
    k=int(s/SEGMENT);a=s-k*SEGMENT
    if a<=1:
        x=1+a;y=.5;psi=0.;curvature=0.
    else:
        t=-np.pi/2+2*(a-1)
        x=2+.5*np.cos(t);y=1+.5*np.sin(t);psi=t+np.pi/2;curvature=2.
    for _ in range(k):x,y=3-y,x
    return x,y,psi+k*np.pi/2,curvature

@njit(cache=True)
def project(x,y):
    best=1e9;bs=0.;be=0.
    xx=x;yy=y
    for k in range(4):
        a=min(1.,max(0.,xx-1));dx=xx-(1+a);dy=yy-.5
        d=dx*dx+dy*dy
        if d<best:best=d;bs=k*SEGMENT+a;be=dy
        t=min(0.,max(-np.pi/2,np.arctan2(yy-1,xx-2)))
        qx=2+.5*np.cos(t);qy=1+.5*np.sin(t)
        dx=xx-qx;dy=yy-qy;d=dx*dx+dy*dy
        if d<best:
            best=d;bs=k*SEGMENT+1+.5*(t+np.pi/2)
            be=-dx*np.cos(t)-dy*np.sin(t)
        xx,yy=yy,3-xx
    return bs,be

def generate_field(seed):
    rng=np.random.default_rng(int(seed))
    direction=int(rng.choice([-1,1]));section=int(rng.integers(4))
    # Four official rotations are represented by start_section metadata; the
    # integration frame rotates the selected parking section onto the bottom.
    single=int(rng.integers(4));single_color=int(rng.choice([-1,1]))
    cards=CARDS
    excluded=9 if single_color==1 else 10
    choices=np.array([i for i in range(1,37) if i!=excluded])
    selected=rng.choice(choices,3,replace=False).tolist()
    rows=[];card_ids=[]
    for k in range(4):
        if k==single:pattern=[[.5,.6,single_color]];card_ids.append(excluded)
        else:
            card=selected.pop(0);pattern=cards[str(card)];card_ids.append(card)
        for a,dist,color in pattern:
            if k==0:dist=.4
            s=k*SEGMENT+float(a)
            x,y,p,_=path(s);e=.5-float(dist)
            rows.append([s,e,float(color),x-e*np.sin(p),y+e*np.cos(p)])
    obs=np.asarray(sorted(rows),dtype=float)
    # Allowed non-parking start in middle zone above the bay. Jitter is only
    # within a collision-free subset, not an invented continuous pillar layout.
    start_s=float(rng.uniform(.58,.62) if direction>0 else rng.uniform(.78,.80))
    start_e=float(rng.uniform(-.020,.020))
    start_heading=float(rng.uniform(-.015,.015))
    return dict(obstacles=obs,direction=direction,start_section=section,
        single_section=(single+section)%4,card_ids=card_ids,
        start_s=start_s,start_e=start_e,start_heading=start_heading,
        field_id=f'{section}:{direction}:'+','.join(map(str,card_ids))+f':{start_s:.9f}:{start_e:.9f}')

def generate_open_wall_geometry(seed):
    """Separate unused Open generator: four official .6/1m corridor draws."""
    rng=np.random.default_rng(seed);w=rng.choice([.6,1.],4)
    return dict(corridor_widths=w,inner_rectangle=(w[3],w[0],3-w[1],3-w[2]))
