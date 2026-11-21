"""Kinematic bicycle, rear-axle reference; footprint centre L/2 ahead of axle.

Midpoint integration avoids heading teleports. Slip reduces effective speed and
yaw response. No inertial tyre/electrical-load calibration is claimed.
"""
import numpy as np
from numba import njit

@njit(cache=True)
def wrap(a):
    return (a+np.pi)%(2*np.pi)-np.pi

@njit(cache=True)
def step_vehicle(x,y,psi,v,delta,dt,slip):
    yaw=v/.1075*np.tan(delta)*(1-.45*slip)
    mid=psi+.5*dt*yaw
    return x+dt*v*np.cos(mid),y+dt*v*np.sin(mid),wrap(psi+dt*yaw)

@njit(cache=True)
def rectangle_collision(x,y,psi,length,bx0,by0,bx1,by1):
    # Exact separating axis test for rotated vehicle rectangle vs aligned box.
    c=np.cos(psi);s=np.sin(psi)
    cx=x+.1075*.5*c;cy=y+.1075*.5*s
    dx=cx-(bx0+bx1)*.5;dy=cy-(by0+by1)*.5
    a=length*.5;b=.064;u=(bx1-bx0)*.5;v=(by1-by0)*.5
    if abs(dx)>a*abs(c)+b*abs(s)+u:return False
    if abs(dy)>a*abs(s)+b*abs(c)+v:return False
    if abs(dx*c+dy*s)>a+u*abs(c)+v*abs(s):return False
    if abs(-dx*s+dy*c)>b+u*abs(s)+v*abs(c):return False
    return True

@njit(cache=True)
def wall_collision(x,y,psi,length):
    c=np.cos(psi);s=np.sin(psi)
    cx=x+.05375*c;cy=y+.05375*s
    rx=.5*length*abs(c)+.064*abs(s)
    ry=.5*length*abs(s)+.064*abs(c)
    return (cx-rx<=0 or cx+rx>=3 or cy-ry<=0 or cy+ry>=3 or
            rectangle_collision(x,y,psi,length,1.,1.,2.,2.))
