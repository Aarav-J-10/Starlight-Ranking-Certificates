"""Released 35/75/105 clamp; servo-command to wheel-angle gain ASSUMED.

Positive mathematical steer=left: delta=(75-u)*gain*pi/180.
A counterfactual has wider command freedom but same physical 38 degree limit.
No simulated mechanical breakage probability rewards software saturation.
"""
import numpy as np
from numba import njit

@njit(cache=True)
def steer(request,old,z,gain,bounded,dt):
    u=75.-request/(1.2*np.pi/180.)
    low=35. if bounded else 15.
    high=105. if bounded else 135.
    clipped=min(high,max(low,u));sat=abs(clipped-u)>1e-9
    q=(75.-clipped)*np.pi/180.
    target=gain*q*(1.-.15*(q/(60.*np.pi/180.))**2)+z[6]*7*np.pi/180.
    target=max(-38*np.pi/180.,min(38*np.pi/180.,target))
    # Nominal mechanical deadband 0.2 road degrees, unmeasured assumption.
    if abs(target)<.2*np.pi/180.:target=0.
    tau=.06+.30*z[7]
    return old+(target-old)*(1-np.exp(-dt/tau)),sat,clipped
