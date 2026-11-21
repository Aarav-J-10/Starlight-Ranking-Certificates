"""Architectural feature matrix. No architecture-dependent outcome factors.

Feature order: repeatable mount, bounded servo, fusion, area gate, magenta
cooldown, direct rear initial parking trigger, heading-terminated parking.
The source has NO robust contextual gate on magenta lap counts. The 7-second
cooldown is retained in C/D; A/B use a conventional rising edge only.
"""
import numpy as np
ARCHITECTURES={
 'A':(0,0,0,0,0,0,0),
 'B':(1,1,0,0,0,0,0),
 'C':(1,1,1,1,1,0,0),
 'D':(1,1,1,1,1,1,1),
 'D_no_mount':(0,1,1,1,1,1,1),
 'D_no_bounds':(1,0,1,1,1,1,1),
 'D_no_fusion':(1,1,0,1,1,1,1),
 'D_no_area_gate':(1,1,1,0,1,1,1),
 'D_no_rear':(1,1,1,1,1,0,1),
 'D_no_heading':(1,1,1,1,1,1,0),
}
ABLATIONS=tuple(k for k in ARCHITECTURES if k.startswith('D_'))

def features(name):
    if name not in ARCHITECTURES:raise ValueError(name)
    return np.asarray(ARCHITECTURES[name],dtype=np.int64)
