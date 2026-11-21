"""Feature-level camera model; score distributions and projection assumed.

Actual HSV-mask-first processing is retained: a missing HSV candidate cannot
be rescued by LAB. A dense wrongly coloured candidate can pass the .55 gate
using .65*HSV alone. The model never claims photorealism/confusion calibration.
Area proxy 18000*(.85/d)^2 is an assumed apparent scale; intrinsics are absent.
"""
import numpy as np
from numba import njit

@njit(cache=True)
def rand(seed,step,channel):
    # Counter-addressable integer hash: invariant to architecture branching.
    x=np.uint64(seed)^np.uint64(step*1009+channel*9176+12345)
    x=(x^(x>>np.uint64(30)))*np.uint64(0xbf58476d1ce4e5b9)
    x=(x^(x>>np.uint64(27)))*np.uint64(0x94d049bb133111eb)
    x=x^(x>>np.uint64(31))
    return float(x>>np.uint64(11))*(1./9007199254740992.)

@njit(cache=True)
def normal(seed,step,channel):
    # Standard-normal Box-Muller, fixed counter channels.
    return np.sqrt(-2*np.log(max(1e-12,rand(seed,step,2*channel))))*np.cos(2*np.pi*rand(seed,step,2*channel+1))

@njit(cache=True)
def candidate(color,distance,z,model,features,seed,frame,obj):
    stabilized=features[0];fusion=features[2]
    mount=model[4] if stabilized else 1.
    pitch=12*z[2]*mount
    geometry_scale=max(.2,1.-.025*pitch)
    maxrange=max(.25,1.15-.025*pitch)
    area=18000*(.85/max(distance,.08))**2*geometry_scale
    if distance>maxrange or model[8]>.5:return 0,0.,area
    n=normal(seed,frame,20+obj)
    hsv=max(0.,min(1.,1.-.55*z[0]-.22*z[4]*abs(n)))
    lab=max(0.,min(1.,1.-.20*z[0]-.12*z[4]*abs(n)))
    lab=hsv+model[10]*(lab-hsv)
    rectangularity=max(.1,.9-.45*z[4]*abs(n)-.008*abs(pitch))
    geom=1. if rectangularity>=.7 else (.75 if rectangularity>=.5 else (.5 if rectangularity>=.35 else .25))
    observed=color
    # Warm-light red -> magenta is shared by every architecture; LAB does not
    # override the class produced by HSV thresholding.
    if color==-1 and rand(seed,frame,100+obj)<min(.95,model[1]*z[1]*(.2+.65*z[0])):
        observed=2;hsv=max(hsv,.88);lab=.08
    elif rand(seed,frame,160+obj)<.035*z[4]*model[1]:
        observed=-color
    if hsv<.05:return 0,0.,area
    confidence=.65*hsv+.20*lab+.15*geom if fusion else hsv
    threshold=.55
    if confidence<threshold or area<120:return 0,confidence,area
    if observed in (-1,1) and features[3] and area<18000:return 0,confidence,area
    # A/B still require visible colour; use an equal nominal actionable range
    # so removing area gating does not grant supernatural long-range sensing.
    if observed in (-1,1) and not features[3] and distance>.85:return 0,confidence,area
    return observed,confidence,area

@njit(cache=True)
def wall_measurement(z,model,features,seed,frame):
    mount=model[4] if features[0] else 1.
    bias=mount*(.04*z[3]+.006*z[2])
    noise=.06*z[4]*normal(seed,frame,3)
    # Loss is derived from wall evidence confidence/visibility, not architecture
    # mission-success multipliers.
    score=1.-.6*z[0]-.35*z[4]*abs(normal(seed,frame,5))-.15*abs(z[2])*mount
    lost=score<.25 or model[8]>.5
    return bias+noise,lost
