"""Exploratory shared-controller feasibility search. NOT research results."""
import numpy as np
from numba import njit
from .vehicle import rectangle_collision

@njit(cache=True)
def feasible(r1,r2,theta,goalx,goaly,direction):
    goal=goalx-direction*.05375
    x0=goal+direction*(r1+r2)*np.sin(theta)
    y0=goaly+(r1+r2)*(1-np.cos(theta))
    if y0<.267 or y0>.55:return False
    for phase in range(2):
        for j in range(81):
            if phase==0:
                a=theta*j/80
                x=x0-direction*r1*np.sin(a);y=y0-r1*(1-np.cos(a))
            else:
                a=theta*(1-j/80)
                x=x0-direction*(r1*np.sin(theta)+r2*(np.sin(theta)-np.sin(a)))
                y=y0-r1*(1-np.cos(theta))-r2*(np.cos(a)-np.cos(theta))
            p=a if direction==1 else np.pi-a
            if rectangle_collision(x,y,p,.25,1.605,0,1.625,.2) or rectangle_collision(x,y,p,.25,2.,0,2.02,.2):return False
            c=x+.05375*np.cos(p);cy=y+.05375*np.sin(p)
            if cy-.125*abs(np.sin(p))-.064*abs(np.cos(p))<=0:return False
    return True

@njit(cache=True)
def feasible3(r1,r2,r3,theta,beta,goalx,goaly,direction):
    goal=goalx-direction*.05375
    dx=-r1*np.sin(theta)-r2*(np.sin(theta)-np.sin(beta))+r3*np.sin(beta)
    dy=-r1*(1-np.cos(theta))-r2*(np.cos(beta)-np.cos(theta))+r3*(1-np.cos(beta))
    x0=goal-direction*dx;y0=goaly-dy
    if y0<.267 or y0>.55:return False
    x=x0;y=y0
    for phase in range(3):
        for j in range(81):
            if phase==0:
                a=theta*j/80
                x=x0-direction*r1*np.sin(a);y=y0-r1*(1-np.cos(a))
            elif phase==1:
                a=theta-(theta-beta)*j/80
                x=x0-direction*(r1*np.sin(theta)+r2*(np.sin(theta)-np.sin(a)))
                y=y0-r1*(1-np.cos(theta))-r2*(np.cos(a)-np.cos(theta))
            else:
                a=beta*(1-j/80)
                xm=x0-direction*(r1*np.sin(theta)+r2*(np.sin(theta)-np.sin(beta)))
                ym=y0-r1*(1-np.cos(theta))-r2*(np.cos(beta)-np.cos(theta))
                x=xm+direction*r3*(np.sin(beta)-np.sin(a));y=ym+r3*(np.cos(a)-np.cos(beta))
            p=a if direction==1 else np.pi-a
            if rectangle_collision(x,y,p,.25,1.605,0,1.625,.2) or rectangle_collision(x,y,p,.25,2.,0,2.02,.2):return False
            cy=y+.05375*np.sin(p)
            if cy-.125*abs(np.sin(p))-.064*abs(np.cos(p))<=0:return False
    return True

if __name__=='__main__':
    for d in [1,-1]:
        found=[]
        rmin1=.1075/np.tan(np.deg2rad(27 if d==1 else 36))
        rmin2=.1075/np.tan(np.deg2rad(36 if d==1 else 27))
        for r1 in np.linspace(rmin1,.32,6):
            for r2 in np.linspace(rmin2,.32,6):
                for th in np.deg2rad(np.arange(40,86,5)):
                    for beta in np.deg2rad(np.arange(5,36,5)):
                        for gy in [.09,.10,.11]:
                            if feasible3(r1,r2,rmin1,th,beta,1.8125,gy,d):found.append((r1,r2,np.rad2deg(th),np.rad2deg(beta),gy))
        print(d,len(found),found[:20])
