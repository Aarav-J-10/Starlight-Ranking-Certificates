"""All range/distribution choices below are SIMULATION-ASSUMED stress tests.

z order: illumination, ambiguity, camera pitch, camera lateral offset, sensor
noise, latency, steering offset, steering lag, battery loss, wheel slip.
Signed dimensions 2,3,6 have support [-1,1]; all others [0,1].
Nominal z=0 means zero added disturbance, not zero baseline actuator dynamics.
"""
import numpy as np
NAMES=('illumination','ambiguity','camera_pitch','camera_offset','sensor_noise',
       'latency','steering_offset','steering_lag','battery_loss','slip')
SIGNED=(2,3,6)
PHYSICAL_NAMES=('illumination_shift','color_ambiguity','camera_pitch_error_deg',
 'camera_offset_m','sensor_noise_m','latency_ms','steering_offset_deg',
 'steering_lag_s','battery_factor','slip_factor')

def physical(z):
    z=np.asarray(z)
    return dict(zip(PHYSICAL_NAMES,[z[0],z[1],12*z[2],.04*z[3],.06*z[4],
          50+350*z[5],7*z[6],.06+.30*z[7],1-.45*z[8],.30*z[9]]))

def validate_z(z):
    z=np.asarray(z,dtype=float)
    if z.shape != (10,) or not np.all(np.isfinite(z)): raise ValueError('z must be 10 finite values')
    lo=np.zeros(10);lo[list(SIGNED)]=-1
    if np.any(z<lo) or np.any(z>1): raise ValueError('Disturbance out of declared range')
    return z
