"""Executable feature-level source-informed surrogate, not a validated twin.

Common bridges: geometric pursuit replaces unavailable image projection;
initial car is in the official middle zone (released inside_park=True requires
an alternate start adaptation); one initial magenta count maps released four
counts to three completed laps; the undefined parking API is conceptually
linked to the available helper. Special source heading loops are represented
by physically integrated, nominally equivalent reverse arcs. All variants can
execute these arcs; A-C terminate by nominal duration, D by relative heading.
Rear camera changes the approach trigger only, then is closed as in release.
No exact-target position correction or probability-only parking is used.
"""
import numpy as np
from numba import njit
from .config import model_array,MAX_TIME
from .disturbances import validate_z,physical
from .environment import generate_field,path,project,PERIMETER
from .vehicle import step_vehicle,wall_collision,rectangle_collision,wrap
from .actuator import steer
from .power_model import speed_step
from .perception import candidate,wall_measurement,normal
from .controller import navigation_request,desired_offset
from .state_machine import features,ABLATIONS
from .metrics import FAILURES,CHAINS

@njit(cache=True)
def _mission(obs,direction,start_s,start_e,start_h,z,m,f,noise_seed,save_trace):
    dt=m[6];length=m[7];nsteps=int(MAX_TIME/dt)
    records=np.zeros((nsteps if save_trace else 1,12))
    x,y,psi,_=path(start_s);x-=start_e*np.sin(psi);y+=start_e*np.cos(psi)
    if direction<0:psi+=np.pi
    psi=wrap(psi+start_h);v=0.;delta=0.;progress=0.;old_s=start_s
    seen=np.zeros(len(obs));passed=np.zeros(len(obs),dtype=np.int64)
    # Obstacles behind the initial pose count after their next course encounter.
    next_pass=np.empty(len(obs))
    for j in range(len(obs)):next_pass[j]=(direction*(obs[j,0]-start_s))%PERIMETER
    latency=.05+.35*z[5];delay=int(round(latency/dt));buffer=np.zeros(64);vbuffer=np.zeros(64)
    dropout=0;saturation=0;sat_prev=False;loss_time=0.;maxerror=0.;sumerror=0.
    magenta_count=1;lastmag=-1.;was_magenta=False;confusions=0;false_events=0
    mission_code=5;chain=0;state=0;phase_time=0.;phase_yaw=0.;n=0
    park_trigger_error=0.;parking_started=False;handed=False;nav_duration=np.nan
    yaw0=0. if direction>0 else np.pi
    # Seventy-degree arcs are an explicitly assumed geometric bridge; source
    # fifty-degree/timed multi-stage manoeuvre lacks measured motion mapping.
    theta=m[11]*np.pi/180.
    d1=(-36. if direction>0 else 38.)*np.pi/180.
    d2=(38. if direction>0 else -36.)*np.pi/180.
    r1=.1075/abs(np.tan(d1));r2=.1075/abs(np.tan(d2))
    # Analytic common nominal reverse-arc setup; nominal output is not fitted
    # to retained physical timings or failures.
    parkx=2.-.75*length-direction*m[12]
    targetrear=parkx-direction*.05375
    setupx=targetrear+direction*(r1+r2)*np.sin(theta)
    setupy=.10+(r1+r2)*(1-np.cos(theta))
    park_speed=.14*m[3]
    dur1=r1*theta/.14;dur2=r2*theta/.14
    shift_progress=3*PERIMETER-1.
    navigation_progress=0.
    no_seen_on_failure=0
    # Previous rear-axle pose for continuous pillar-plane crossing adjudication.
    oldx=x;oldy=y;oldpsi=psi
    for i in range(nsteps):
        t=i*dt;n=i+1
        s,e=project(x,y)
        ds=(s-old_s+PERIMETER/2)%PERIMETER-PERIMETER/2
        progress+=direction*ds;old_s=s
        tracking=abs(e-desired_offset(s,obs,seen))
        maxerror=max(maxerror,tracking);sumerror+=tracking
        request=0.;targetv=.55*m[3];frame=int((t+1e-9)/.08)
        fresh_frame=i==0 or frame>int((t-dt+1e-9)/.08)
        if state==0:
            navigation_progress=progress
            wall_error,lost=wall_measurement(z,m,f,noise_seed,frame)
            if lost:
                if fresh_frame:dropout+=1
                loss_time+=dt
            else:loss_time=0.
            if loss_time>2.:
                mission_code=8;chain=6;break
            magenta=False
            for j in range(len(obs)):
                ahead=(direction*(obs[j,0]-s)+PERIMETER/2)%PERIMETER-PERIMETER/2
                if -.28<ahead<1.25 and fresh_frame:
                    seenclass,confidence,area=candidate(int(obs[j,2]),max(.08,ahead),z,m,f,noise_seed,frame,j)
                    if ahead>0:
                        if seenclass==2:
                            confusions+=1;magenta=True;seen[j]=0
                        elif seenclass!=0:seen[j]=seenclass*direction
                        else:
                            dropout+=1
                            # Real frame-to-frame target selection has no perfect
                            # map memory; short hold only avoids empty-frame jumps.
                            if confidence<.20:seen[j]=0
                elif ahead<-.28 or ahead>1.25:seen[j]=0
                # Judge the side at the crossing itself, not after the vehicle
                # has cleared and possibly returned toward the lane centre.
                # The progress window selects this lap's expected encounter;
                # travel-oriented body-centre plane crossing gives its instant.
                if abs(progress-next_pass[j])<.40 and passed[j]<3:
                    px,py,pp,_=path(obs[j,0])
                    pcx=oldx+.05375*np.cos(oldpsi)
                    pcy=oldy+.05375*np.sin(oldpsi)
                    ccx=x+.05375*np.cos(psi)
                    ccy=y+.05375*np.sin(psi)
                    previous_plane=direction*((pcx-px)*np.cos(pp)+(pcy-py)*np.sin(pp))
                    current_plane=direction*((ccx-px)*np.cos(pp)+(ccy-py)*np.sin(pp))
                    if previous_plane<=0. and current_plane>0.:
                        fraction=-previous_plane/(current_plane-previous_plane)
                        crossx=oldx+fraction*(x-oldx)
                        crossy=oldy+fraction*(y-oldy)
                        crosspsi=oldpsi+fraction*wrap(psi-oldpsi)
                        cx=crossx+.05375*np.cos(crosspsi)
                        cy=crossy+.05375*np.sin(crosspsi)
                        lateral=-(cx-px)*np.sin(pp)+(cy-py)*np.cos(pp)
                        relative=crosspsi-pp
                        # Half-width of the rotated rectangle's transverse
                        # slice through its centre; exact at this crossing.
                        slice_half=min((.5*length+.005)/max(1e-12,abs(np.sin(relative))),
                                       .069/max(1e-12,abs(np.cos(relative))))
                        if rectangle_collision(crossx,crossy,crosspsi,length,
                             obs[j,3]-.025,obs[j,4]-.025,obs[j,3]+.025,obs[j,4]+.025):
                            mission_code=2;chain=2;no_seen_on_failure=int(seen[j]==0);break
                        sign=obs[j,2]*direction
                        if (lateral-obs[j,1])*sign < .025+slice_half:
                            mission_code=3;chain=4;break
                        passed[j]+=1;next_pass[j]+=PERIMETER
            if mission_code in (2,3):break
            # Course marking is exact geometry; appearance depends on lighting,
            # noise and pitch. Blue/orange marks exist as non-actionable cues in
            # Obstacle_Challenge.py; they do not secretly supply lap truth.
            distcue=abs((s-start_s+PERIMETER/2)%PERIMETER-PERIMETER/2)
            true_mag=distcue<.13 and progress>.5
            if true_mag:
                evidence=1-.50*z[0]-.30*z[4]*abs(normal(noise_seed,frame,290))
                magenta=magenta or (evidence>.55 and not lost)
            # Conventional baselines use rising edge + same seven-second debounce;
            # released C/D accept persistent presence after cooldown (no edge).
            accepted=magenta and t-lastmag>7 and (f[4] or not was_magenta)
            if accepted:
                magenta_count+=1;lastmag=t
                if not true_mag:false_events+=1
            was_magenta=magenta
            if magenta_count>=4 and progress<3*PERIMETER-.35:
                mission_code=4;chain=1;break
            if progress>3*PERIMETER+.5 and magenta_count<4:
                mission_code=4;chain=7;break
            request=navigation_request(x,y,psi,s,direction,obs,seen,wall_error if not lost else 0.)
            if lost:request=direction*5*.9*np.pi/180.
            # Final approach shifts toward outer parking geometry only after
            # the third-lap start section is reached (source handoff abstraction).
            if parking_started or (progress>shift_progress and np.all(passed>=3) and y<.70 and abs(wrap(psi-yaw0))<.6):
                blend=min(1.,max(0.,(progress-shift_progress)/.35))
                target_s=s+direction*.20
                tx,ty,tp,_=path(target_s)
                offset=blend*(setupy-.5)
                tx-=offset*np.sin(tp);ty+=offset*np.cos(tp)
                # On the parking straight, continue to the analytic setup
                # rather than beginning the next rounded corner.
                if y<.70 and abs(wrap(psi-yaw0))<.6:
                    tx=x+direction*.10;ty=setupy
                alpha=wrap(np.arctan2(ty-y,tx-x)-psi)
                request=np.arctan2(2*.1075*np.sin(alpha),max(.1,np.sqrt((tx-x)**2+(ty-y)**2)))
                targetv=.25*m[3]
                if not parking_started:
                    parking_started=True
                    mount=m[4] if f[0] else 1.
                    # Ground-plane trigger conditioning, ASSUMED not measured.
                    scale=m[9] if f[5] else 1.
                    park_trigger_error=m[5]*scale*(mount*(.03*z[2]+.04*z[3])+.04*z[4]*normal(noise_seed,0,400))
                if direction*(x-(setupx-direction*.25*(.18+.05)+direction*park_trigger_error))>=0:
                    if progress<3*PERIMETER-.35 or magenta_count<4:
                        mission_code=4;chain=7;break
                    state=1;phase_time=0.;handed=True;nav_duration=t
            if progress<-.30:mission_code=4;chain=3;break
        else:
            phase_time+=dt
            # Braking and servo settling preserve noninstantaneous speed/steer.
            if state==1:
                targetv=0.;request=0.
                if phase_time>=1.:state=2;phase_time=0.
            elif state==2:
                targetv=0.;request=d1
                if phase_time>=1.:state=3;phase_time=0.;phase_yaw=psi
            elif state==3:
                targetv=-park_speed;request=d1
                turned=abs(wrap(psi-phase_yaw))
                # Timed baseline includes the same nominal motor startup delay.
                braking_yaw=abs(v/.1075*np.tan(delta))*(.18+.05)
                stop=turned+braking_yaw>=theta if f[6] else phase_time>=dur1
                if stop:state=4;phase_time=0.
                elif phase_time>12.:mission_code=6;chain=5;break
            elif state==4:
                targetv=0.;request=d1
                if phase_time>=1.:state=5;phase_time=0.
            elif state==5:
                targetv=0.;request=d2
                if phase_time>=1.:state=6;phase_time=0.;phase_yaw=psi
            elif state==6:
                targetv=-park_speed;request=d2
                turned=abs(wrap(psi-phase_yaw))
                # D uses current heading relative to final desired road heading,
                # like the source's second reverse heading loop.
                braking_yaw=abs(v/.1075*np.tan(delta))*(.18+.05)
                stop=abs(wrap(psi-yaw0))<=braking_yaw+.005 if f[6] else phase_time>=dur2
                if stop:state=7;phase_time=0.
                elif phase_time>12.:mission_code=6;chain=5;break
            elif state==7:
                targetv=0.;request=d2
                if phase_time>=1.:
                    c=np.cos(psi);sn=np.sin(psi)
                    cx=x+.05375*c;cy=y+.05375*sn
                    rx=(.5*length+.005)*abs(c)+.069*abs(sn)
                    ry=(.5*length+.005)*abs(sn)+.069*abs(c)
                    good=(navigation_progress>=3*PERIMETER and np.all(passed>=3) and cx-rx>=2-1.5*length and cx+rx<=2 and cy-ry>=0 and cy+ry<=.2 and
                          abs(np.sin(wrap(psi-yaw0)))*.1075<=.02)
                    mission_code=0 if good else 6;chain=0 if good else 5
                    break
        # Queue the requested steering. Delay is applied to the entire controller
        # pipeline, including parking phase switches, for every architecture.
        buffer[i%64]=request
        vbuffer[i%64]=targetv
        delayed=buffer[(i-delay)%64] if i>=delay else 0.
        delayedv=vbuffer[(i-delay)%64] if i>=delay else 0.
        delta,sat,u=steer(delayed,delta,z,m[0],bool(f[1]),dt)
        if sat and not sat_prev:saturation+=1
        sat_prev=sat
        v=speed_step(v,delayedv,z,m[2],dt)
        oldx=x;oldy=y;oldpsi=psi
        x,y,psi=step_vehicle(x,y,psi,v,delta,dt,.30*z[9])
        # Substep swept footprint at midpoint and endpoint, not centre-only.
        for sub in range(2):
            frac=.5 if sub==0 else 1.
            qx=oldx+frac*(x-oldx);qy=oldy+frac*(y-oldy);qp=oldpsi+frac*wrap(psi-oldpsi)
            if wall_collision(qx,qy,qp,length):mission_code=1;chain=3;break
            for j in range(len(obs)):
                if abs(qx-obs[j,3])<.25 and abs(qy-obs[j,4])<.25:
                    if rectangle_collision(qx,qy,qp,length,obs[j,3]-.025,obs[j,4]-.025,obs[j,3]+.025,obs[j,4]+.025):
                        mission_code=2;chain=2;no_seen_on_failure=int(seen[j]==0);break
            if mission_code==2:break
            left=2-1.5*length
            if rectangle_collision(qx,qy,qp,length,left-.02,0,left,.2) or rectangle_collision(qx,qy,qp,length,2.,0,2.02,.2):
                mission_code=6;chain=5;break
        if save_trace:records[i]=np.array([t,x,y,psi,v,delta,progress,float(state),float(magenta_count),request,e,u])
        if mission_code in (1,2,6):break
        if abs(v/.1075*np.tan(delta))>8.:mission_code=7;chain=3;break
    duration=(n-1)*dt
    values=np.array([float(mission_code),duration,maxerror,sumerror/max(n,1),float(dropout),float(saturation),
        1. if mission_code==0 else 0.,progress,float(confusions),float(false_events),float(chain),1. if handed else 0.,
        nav_duration,float(no_seen_on_failure),float(n),x,y,psi,float(magenta_count)])
    return values,records[:n] if save_trace else records

def simulate(seed,architecture,z,model=None,trace=False,noise_seed=None):
    z=validate_z(z);m=model_array(model);field=generate_field(seed)
    ns=(int(seed)^0x5A17C0DE) if noise_seed is None else int(noise_seed)
    vals,tr=_mission(field['obstacles'],field['direction'],field['start_s'],field['start_e'],
      field['start_heading'],z,m,features(architecture),ns,bool(trace))
    code=int(vals[0]);ok=code==0
    out=dict(scenario_seed=int(seed),noise_seed=ns,architecture=architecture,field_id=field['field_id'],
      travel_direction='CCW' if field['direction']>0 else 'CW',start_section=field['start_section'],
      start_condition='middle_zone_above_parking',start_s_m=field['start_s'],start_lateral_m=field['start_e'],
      obstacle_count=len(field['obstacles']),cards=','.join(map(str,field['card_ids'])),
      mission_success=int(ok),failure_code=FAILURES[code],completion_time=float(vals[1]) if ok else np.nan,
      duration=float(vals[1]),penalized_completion_time=float(vals[1]) if ok else MAX_TIME,
      max_lateral_error=float(vals[2]),mean_lateral_error=float(vals[3]),perception_dropouts=int(vals[4]),
      saturation_events=int(vals[5]),parking_success=int(vals[6]),progress_m=float(vals[7]),
      color_confusion_events=int(vals[8]),false_course_events=int(vals[9]),causal_chain=CHAINS[int(vals[10])],
      parking_attempted=int(vals[11]),navigation_duration=float(vals[12]),
      missing_target_at_collision=int(vals[13]),steps=int(vals[14]),final_x=float(vals[15]),
      final_y=float(vals[16]),final_heading=float(vals[17]),course_count=int(vals[18]))
    out.update(physical(z))
    if trace:out['trace']=tr;out['obstacles']=field['obstacles']
    return out

def simulate_batch(seeds,architecture,zs,model=None,noise_seeds=None):
    if len(seeds)!=len(zs):raise ValueError('Seed/z row counts differ')
    if noise_seeds is None:noise_seeds=[None]*len(seeds)
    return [simulate(int(seed),architecture,z,model=model,noise_seed=ns) for seed,z,ns in zip(seeds,zs,noise_seeds)]
