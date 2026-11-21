"""Shared geometric pursuit bridge for absent camera intrinsics/image masks.

The same pursuit and nominal speed are used by all variants. This is not a
literal reproduction of released KP=.014 pixel steering. It represents the
wall reference plus continuously updated colour-selected lateral targets.
"""
import numpy as np
from numba import njit
from .environment import path,PERIMETER
from .vehicle import wrap

@njit(cache=True)
def desired_offset(s,obs,seen):
    total=0.;weight=0.
    for j in range(len(obs)):
        if seen[j]==-1 or seen[j]==1:
            d=(s-obs[j,0]+PERIMETER/2)%PERIMETER-PERIMETER/2
            if abs(d)<.65:
                w=np.exp(-.5*(d/.24)**2)
                target=obs[j,1]+seen[j]*.175
                total+=w*target;weight+=w
    if weight<=0:return 0.
    return total/max(1.,weight)

@njit(cache=True)
def navigation_request(x,y,psi,s,direction,obs,seen,wall_error):
    ahead=.23
    ts=s+direction*ahead
    tx,ty,tp,_=path(ts)
    e=desired_offset(ts,obs,seen)+wall_error
    tx-=e*np.sin(tp);ty+=e*np.cos(tp)
    alpha=wrap(np.arctan2(ty-y,tx-x)-psi)
    distance=max(.10,np.sqrt((tx-x)**2+(ty-y)**2))
    return np.arctan2(2*.1075*np.sin(alpha),distance)
