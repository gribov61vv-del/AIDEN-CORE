# ZHULKOR / R.R.E.M. — numerical baseline

## Source model preserved
The implementation follows the supplied abstract dynamical energy-memory model: x1, x2, memory, feedback_state; 100 Hz input; disturbance from 0.45 to 0.455 s; coupling, damping, memory accumulation and decay; supplied parameter defaults.

## Numerical change
The original script used forward Euler. With omega0 = 2*pi*1000 rad/s and dt = 1e-5 s, omega0*dt is about 0.0628. Forward Euler introduces artificial amplitude growth for oscillatory modes. This implementation uses classical fourth-order Runge–Kutta (RK4), evaluating the supplied differential equations at intermediate stages. A conservative resolution guard rejects omega0*dt > 0.5.

The differential equations are retained. RK4 improves numerical integration; it does not validate the physical model.

## Dimensional and physical caveats
1. x1, x2 and memory enter the supplied energy expression as a sum of squares without declared units or normalization. energy_scale_J therefore labels a model-defined energy scale, not demonstrated physical joules.
2. interaction_energy_J*(abs(x1)+abs(memory))/dt is retained as an interaction-power index. A physical power balance needs defined interaction mechanisms and dimensionally consistent states.
3. peak/recovery_efficiency is retained as the source model's recovery estimate convention. It is not derived from a measured recovery process.
4. The model has no explicit energy reservoir or conservation equation. Do not interpret its energy diagnostic as conserved total energy.
5. Defaults are illustrative and require experimental calibration.

## Run
    cd ~/AIDEN-CORE/triad_engine
    python -m unittest -v test_zhulkor_rrem.py
    python zhulkor_rrem.py
    python zhulkor_rrem.py --dt 5e-6 --duration 1.0 --output zhulkor_halfstep.csv

Compare dt and dt/2 outputs. Numerical convergence supports solver consistency for these equations, not the physical truth of the equations.

## Boundary with TRIAD-GEO
R.R.E.M. and TRIAD-GEO remain separate modules. A future coupling experiment must define an explicit mapping from R.R.E.M. states to graph nodes/edge constraints, document units, and test predictive value. No coupling is assumed here.


## Termux baseline run and step-refinement experiment

The default one-second run completed with RK4 and 100,001 samples:
- peak model-defined energy scale: 2.918916e-12 (labelled J by the supplied scale parameter, but not physically validated);
- average interaction-power index: 8.054543e-13 (the index is step-dependent; see below);
- final memory: 1.607866e-02.

Step refinement on the same one-second interval:

| dt (s) | samples | peak energy scale | final memory | average interaction-power index |
|---:|---:|---:|---:|---:|
| 1.0e-5 | 100,001 | 2.918916e-12 | 1.607866e-2 | 8.054543e-13 |
| 5.0e-6 | 200,001 | 2.915453e-12 | 1.607863e-2 | 1.610905e-12 |
| 2.5e-6 | 400,001 | 2.913771e-12 | 1.607831e-2 | 3.221659e-12 |

The state-memory output is stable to the shown precision under step refinement. The peak energy diagnostic changes by about 0.18% from the coarsest to finest run. This is a numerical refinement check, not experimental validation.

**Important finding:** the supplied interaction-power expression divides by dt, while the reported average is an arithmetic mean over samples. Halving dt approximately doubles this average. Therefore it is not currently a timestep-invariant physical power estimate. It is retained as a source-defined diagnostic and explicitly labelled an index. Before interpreting it as watts, define the interaction-energy accounting per step and test the time-integrated quantity for timestep invariance.

The recovery estimate peak/recovery_efficiency is also a convention from the source model, not a derived thermodynamic result.
