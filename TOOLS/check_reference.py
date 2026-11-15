#!/usr/bin/env python3
"""Starlight code-recovery package: read-only baseline schema and metrics audit.
No third-party deps; no experiment hardware; no provenance claims.
"""
from __future__ import annotations
import csv, json, statistics, math
from pathlib import Path

P=Path(__file__).resolve().parents[1]
BASE=P/'REFERENCE_DATA'/'starlight-iris-2026'
S=json.loads((P/'CONTRACTS'/'CSV_SCHEMAS.json').read_text())
E=json.loads((P/'CONTRACTS'/'EXPECTED_RESULTS.json').read_text())
N=0

def check(cond, msg):
 global N
 N+=1
 if not cond:raise AssertionError(msg)

def rows(key):
 with (BASE/key).open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  check(reader.fieldnames==S[key]['columns'], f'Header mismatch: {key}')
  r=list(reader)
  check(len(r)==S[key]['rows'], f'Historical row count mismatch: {key}')
  return r

def p95(a):
 a=sorted(float(x) for x in a)
 y=(len(a)-1)*0.95; lo=math.floor(y);hi=math.ceil(y)
 return a[lo]+(a[hi]-a[lo])*(y-lo)

def close(a,b,tol=1e-5):return abs(a-b)<=tol

def main():
 for key in S: rows(key)
 g=rows('simulation/primary_grid.csv'); c=rows('simulation/confirmation.csv'); m=rows('simulation/model_forms.csv')
 check({k:sum(x['certificate_label']==k for x in g) for k in ('A','D','unresolved')}==E['simulation']['grid_certificates'],'primary classifications')
 for key, r in [('grid',g),('confirmation',c),('models',m)]:
  for x in r:
   n=int(x['n_pairs']);pl=int(x['n_plus']);mi=int(x['n_minus'])
   check(n>0 and 0<=pl+mi<=n, f'{key}: invalid paired discordance counts')
   check(close(100*(pl-mi)/n,float(x['delta_pp']),1e-6),f'{key}: delta mismatch at {x}')
   lo=float(x['ci_low_pp']);hi=float(x['ci_high_pp'])
   check(lo<=float(x['delta_pp'])<=hi,f'{key}: point estimate not in interval')
   label='A' if lo>0 else 'D' if hi<0 else 'unresolved'
   check(label==x['certificate_label'],f'{key}: inconsistent interval sign label')
 check(sum(int(x['missions_executed']) for x in g)==528000,'grid mission count')
 check(sum(int(x['missions_executed']) for x in c)==128000,'confirmation mission count')
 check(sum(int(x['missions_executed_additional']) for x in m)==96000,'model missions')
 check(528000+128000+96000==752000,'total mission count')
 for x in c:
  if close(float(x['gain_g']),1.2) and close(float(x['stress_s']),.03) and close(float(x['timestep_s']),.04):check(int(x['n_plus'])==90 and int(x['n_minus'])==6,'confirmation witness 1.2')
  if close(float(x['gain_g']),1.26) and close(float(x['stress_s']),.03) and close(float(x['timestep_s']),.04):check(int(x['n_plus'])==59 and int(x['n_minus'])==293,'confirmation witness 1.26')
 a=rows('physical/wp1/emergency_stop_trips.csv')
 check(sum(int(x['motor_cut_confirmed']) for x in a)==23,'WP1 overall motor cut')
 check(all(int(x['motor_cut_confirmed'])==1 for x in a if x['cohort']=='initial_gate'),'WP1 initial gate')
 check(close(statistics.mean(float(x['cut_latency_ms']) for x in a if x['cut_latency_ms']),14.195652173913043,1e-5),'WP1 success-only mean')
 b=rows('physical/wp2/steering_calibration.csv'); sx=[float(x['servo_command'])-75 for x in b];sy=[float(x['protractor_angle_deg']) for x in b]
 mx=statistics.mean(sx);my=statistics.mean(sy)
 slope=sum((x-mx)*(y-my) for x,y in zip(sx,sy))/sum((x-mx)**2 for x in sx)
 check(close(slope,1.238,0.001),'WP2 steering slope')
 a=rows('physical/wp2/latency_events.csv');check(close(p95([x['latency_ms'] for x in a]),28.16,0.001),'WP2 p95')
 check(sum(float(x['latency_ms'])>33 for x in a)==3,'WP2 missed33')
 check(sum(float(x['latency_ms'])>50 for x in a)==0,'WP2 missed50')
 a=rows('physical/wp3/dock_camera_accuracy.csv');check(close(p95([x['position_error_mm'] for x in a]),2.48,.001),'WP3 position p95')
 check(close(p95([x['heading_error_deg'] for x in a]),1.286,.001),'WP3 heading p95')
 a=rows('physical/wp4/clock_compass_pairs.csv');groups={}
 for x in a:groups.setdefault((x['session'],x['condition'],x['controller']),[]).append(float(x['heading_shift_deg']))
 for k,v in E['physical']['wp4']['means'].items():
  session,condition=('dial_pilot','mismatch') if k=='dial_pilot_mismatch' else ('linkage_consolidated',k.replace('linkage_consolidated_',''))
  for ctl,mean in v.items():check(close(statistics.mean(groups[(session,condition,ctl)]),mean,.005),f'WP4 {k}/{ctl}')
 a=rows('physical/wp5_wp6/docking_session_summary.csv')
 check(sum(int(x['n_pairs']) for x in a)==60 and sum(int(x['clock_success']) for x in a)==41 and sum(int(x['compass_success']) for x in a)==53,'WP5 totals')
 a=rows('physical/wp5_wp6/independent_audit.csv')
 check(sum(int(x['agreement']) for x in a)==8 and sum(int(x['unsupported_winner']) for x in a)==1,'WP6 audit')
 a=rows('physical/wp7/linkage_ABA.csv')
 for phase,expected in E['physical']['wp7']['mean_gain'].items():check(close(statistics.mean(float(x['measured_gain_response']) for x in a if x['phase']==phase),expected,.0001),'WP7 gain '+phase)
 for phase,expected in E['physical']['wp7']['mean_current'].items():check(close(statistics.mean(float(x['servo_current_A']) for x in a if x['phase']==phase),expected,.0001),'WP7 current '+phase)
 a=rows('physical/wp8/colour_sorter.csv')
 for r,expected in [(k,E['physical']['wp8'][k]) for k in ('S1_fixed','S2_calibrated','S3_recheck')]:
  sub=[x for x in a if x['recipe']==r]
  check(sum(int(x['n_correct']) for x in sub)==expected['correct'] and sum(int(x['n_items']) for x in sub)==expected['total'],'WP8 recipe '+r)
 a=rows('physical/d1/shared_failure_60pair.csv')
 check({k:sum(x['outcome']==k for x in a) for k in ('both_succeed','both_fail','clock_only','compass_only')}=={k:v for k,v in E['physical']['d1_60'].items() if k!='pairs'},'D1 small counts')
 a=rows('physical/d1/extended_shared_failure_pairs.csv')
 check({k:sum(x['outcome']==k for x in a) for k in ('both_fail','clock_only','compass_only')}=={k:v for k,v in E['physical']['d1_extended'].items() if k!='failure_bearing_pairs'},'D1 extended counts')
 print(f'PASS: {N} read-only reference schema / numerical checks. Original observations and simulator generator are NOT authenticated.')

if __name__=='__main__':main()
