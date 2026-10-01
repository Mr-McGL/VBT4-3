#!/usr/bin/env python3
"""Ejemplo: cuatro entradas externas variables en una simulación Zerlaut."""

from pathlib import Path

import numpy as np
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.coupling import Linear
from tvb.simulator.integrators import HeunDeterministic
from tvb.simulator.monitors import Raw

from parameter_simulator import ParameterSimulator
from run_simulation_simple import (
    BASELINE_HZ,
    DT_MS,
    FI_RATIO,
    INPUT_SCALE,
    PULSE_AMPLITUDE_HZ,
    PULSE_DURATION_MS,
    PULSE_ONSET_MS,
    build_model,
    build_pulse_input,
    save_result,
)


OUTPUT_PATH = Path("results/parameter_simulation.npz")


def pulse_fe_region(time_ms: float) -> float:
    """Entrada excitatoria de una región, en kHz."""
    active = PULSE_ONSET_MS <= time_ms < PULSE_ONSET_MS + PULSE_DURATION_MS
    return INPUT_SCALE * (BASELINE_HZ + PULSE_AMPLITUDE_HZ * active) / 1000.0


def pulse_fi_region(time_ms: float) -> float:
    """Entrada inhibitoria de una región, en kHz."""
    return FI_RATIO * pulse_fe_region(time_ms)


def main() -> None:
    _, stimulus_hz, fe_ext_hz, fi_ext_hz = build_pulse_input()
    model = build_model()
    model.variables_of_interest = model.state_variables

    fe_khz = (fe_ext_hz[:-1] / 1000.0)[:, np.newaxis]
    fi_khz = (fi_ext_hz[:-1] / 1000.0)[:, np.newaxis]
    simulator = ParameterSimulator(
        model=model,
        input_parameters=[
            ("external_input_ex_ex", fe_khz),
            ("external_input_in_ex", [pulse_fe_region]),
            ("external_input_ex_in", fi_khz),
            ("external_input_in_in", [pulse_fi_region]),
        ],
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

    times, states = simulator.run(n_steps=len(fe_khz))[0]
    history = np.vstack((np.zeros((1, 5)), states[:, :, 0, 0]))
    output_path = save_result(
        np.r_[0.0, times], stimulus_hz, fe_ext_hz, fi_ext_hz, history, OUTPUT_PATH
    )
    print(f"Resultado guardado en {output_path}")


if __name__ == "__main__":
    main()
