"""Assumed first-order speed response; no fabricated current/brownout model."""
import numpy as np
from numba import njit

@njit(cache=True)
def speed_step(v,target,z,motor_tau,dt):
    battery=1-.45*z[8]
    slip=.30*z[9]
    equilibrium=target*battery*(1-slip)
    tau=motor_tau*(1+1.5*z[8])
    return v+(equilibrium-v)*(1-np.exp(-dt/tau))
