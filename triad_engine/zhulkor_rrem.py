#!/usr/bin/env python3
"""ZHULKOR / R.R.E.M. abstract dynamical energy-memory research model.

Implements supplied state equations with classical RK4 integration.
Energy fields are model-defined diagnostics, not asserted physical conserved quantities.
Standard library only.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import pi, sin, isfinite
import argparse
import csv

@dataclass
class Params:
    omega0: float = 2*pi*1000
    damping: float = 0.02
    coupling: float = 0.15
    feedback: float = 0.20
    memory_gain: float = 0.10
    memory_decay: float = 0.001
    energy_scale_J: float = 1e-12
    interaction_energy_J: float = 1e-15
    recovery_efficiency: float = 0.50
    dt: float = 1e-5
    duration: float = 1.0

@dataclass
class State:
    x1: float = 0.0
    x2: float = 0.0
    memory: float = 0.0
    feedback_state: float = 0.0

def input_signal(t): return sin(2*pi*100*t)
def disturbance(t): return 1.0 if 0.45 <= t <= 0.455 else 0.0

def derivative(t, s, p):
    u,d=input_signal(t),disturbance(t)
    dx1=s.x2-p.damping*s.x1+p.coupling*(s.feedback_state-s.x1)+u-d
    dx2=-(p.omega0**2)*s.x1-p.damping*s.x2+p.feedback*s.memory
    activity=abs(s.x1)+0.25*abs(s.x2)
    dm=p.memory_gain*activity-p.memory_decay*s.memory
    dfb=-p.feedback*s.feedback_state-d
    return State(dx1,dx2,dm,dfb)

def _combine(s, terms, scale):
    return State(
        s.x1+scale*sum(w*k.x1 for w,k in terms),
        s.x2+scale*sum(w*k.x2 for w,k in terms),
        s.memory+scale*sum(w*k.memory for w,k in terms),
        s.feedback_state+scale*sum(w*k.feedback_state for w,k in terms))

def rk4_step(t,s,p):
    h=p.dt
    k1=derivative(t,s,p)
    k2=derivative(t+h/2,_combine(s,[(0.5,k1)],h),p)
    k3=derivative(t+h/2,_combine(s,[(0.5,k2)],h),p)
    k4=derivative(t+h,_combine(s,[(1.0,k3)],h),p)
    return _combine(s,[(1/6,k1),(1/3,k2),(1/3,k3),(1/6,k4)],h)

def validate(p):
    values=(p.omega0,p.damping,p.coupling,p.feedback,p.memory_gain,p.memory_decay,
            p.energy_scale_J,p.interaction_energy_J,p.recovery_efficiency,p.dt,p.duration)
    if not all(isfinite(v) for v in values): raise ValueError("parameters must be finite")
    if p.omega0<=0 or p.dt<=0 or p.duration<=0: raise ValueError("omega0, dt and duration must be positive")
    if p.damping<0 or p.memory_decay<0 or p.energy_scale_J<0 or p.interaction_energy_J<0:
        raise ValueError("damping, decay and energy scales must be nonnegative")
    if not 0<p.recovery_efficiency<=1: raise ValueError("recovery_efficiency must be in (0, 1]")
    if p.omega0*p.dt>0.5: raise ValueError("omega0*dt exceeds conservative RK4 resolution guard (0.5)")

def run(p):
    validate(p)
    s,rows=State(),[]
    count=int(round(p.duration/p.dt))
    for i in range(count+1):
        t=i*p.dt
        energy=p.energy_scale_J*(s.x1*s.x1+s.x2*s.x2+s.memory*s.memory)
        power_index=p.interaction_energy_J*(abs(s.x1)+abs(s.memory))/p.dt
        row=(t,s.x1,s.x2,s.memory,s.feedback_state,energy,power_index)
        if not all(isfinite(v) for v in row): raise FloatingPointError(f"non-finite state at t={t:.9g}")
        rows.append(row)
        if i<count: s=rk4_step(t,s,p)
    return rows

def summarize(rows,p):
    peak=max(r[5] for r in rows)
    avg=sum(r[6] for r in rows)/len(rows)
    print("=== ZHULKOR / R.R.E.M. (RK4) ===")
    print("Integrator:                       classical RK4")
    print(f"Samples:                          {len(rows)}")
    print(f"Peak stored-state energy scale:   {peak:.6e} J")
    print(f"Average interaction power index:  {avg:.6e} W")
    print(f"Recovery energy estimate:         {peak/p.recovery_efficiency:.6e} J")
    print(f"Final memory state:               {rows[-1][3]:.6e}")
    print("NOTE: energy and recovery are model-defined diagnostics, not a validated physical energy balance.")

def save_csv(rows,path):
    with open(path,"w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f)
        writer.writerow(("t","x1","x2","memory","feedback","energy_scale_J","interaction_power_index_W"))
        writer.writerows(rows)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dt",type=float,default=1e-5)
    parser.add_argument("--duration",type=float,default=1.0)
    parser.add_argument("--output",default="zhulkor_simulation.csv")
    args=parser.parse_args()
    p=Params(dt=args.dt,duration=args.duration)
    rows=run(p); summarize(rows,p); save_csv(rows,args.output)
    print(f"Saved: {args.output}")

if __name__=="__main__": main()
