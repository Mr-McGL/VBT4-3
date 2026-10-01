#!/usr/bin/env python3
"""Simulación Zerlaut de una región con Simulator y Heun de TVB."""

from pathlib import Path

import numpy as np
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.coupling import Linear
from tvb.simulator.integrators import HeunDeterministic
from tvb.simulator.monitors import Raw
from tvb.simulator.simulator import Simulator

from run_simulation_simple import (
    DT_MS,
    build_model,
    build_pulse_input,
    save_result,
    set_external_input,
)


OUTPUT_PATH = Path("results/tvb_full_simulation.npz")


def integrate(
    model, fe_ext_hz: np.ndarray, fi_ext_hz: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Dejar que TVB integre y registre cada tramo de entrada constante."""
    model.variables_of_interest = model.state_variables
    simulator = Simulator(
        model=model,
        connectivity=Connectivity(
            weights=np.zeros((1, 1)),
            tract_lengths=np.zeros((1, 1)),
            centres=np.zeros((1, 3)),
            region_labels=np.array(["región"]),
        ),
        coupling=Linear(a=np.array([0.0])),
        integrator=HeunDeterministic(dt=DT_MS),
        monitors=(Raw(),),
        initial_conditions=np.zeros((1, 5, 1, 1)),
    ).configure()

    # Una llamada por tramo: TVB conserva el estado al pasar del basal al pulso.
    changes = np.flatnonzero(np.diff(fe_ext_hz)) + 1
    boundaries = np.r_[1, changes[changes > 1], fe_ext_hz.size]
    recorded_times = []
    recorded_states = []
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        set_external_input(model, fe_ext_hz[start], fi_ext_hz[start])
        times, states = simulator.run(n_steps=int(end - start))[0]  # Monitor Raw
        recorded_times.append(times)
        recorded_states.append(states[:, :, 0, 0])

    return (
        np.r_[0.0, *recorded_times],
        np.vstack((np.zeros((1, 5)), *recorded_states)),
    )


def main() -> None:
    _, stimulus_hz, fe_ext_hz, fi_ext_hz = build_pulse_input()
    time_ms, history = integrate(build_model(), fe_ext_hz, fi_ext_hz)
    output_path = save_result(
        time_ms, stimulus_hz, fe_ext_hz, fi_ext_hz, history, OUTPUT_PATH
    )
    print(f"Resultado guardado en {output_path}")


if __name__ == "__main__":
    main()
