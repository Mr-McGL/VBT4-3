#!/usr/bin/env python3
"""Simulación Zerlaut de una región con el integrador Heun de TVB."""

from pathlib import Path

import numpy as np
from tvb.simulator.integrators import HeunDeterministic

from run_simulation_simple import (
    DT_MS,
    build_model,
    build_pulse_input,
    save_result,
    set_external_input,
)


OUTPUT_PATH = Path("results/tvb_simulation.npz")


def integrate(model, fe_ext_hz: np.ndarray, fi_ext_hz: np.ndarray) -> np.ndarray:
    integrator = HeunDeterministic(dt=DT_MS)
    integrator.configure()
    state = np.zeros((5, 1, 1), dtype=np.float64)
    history = np.zeros((fe_ext_hz.size, 5), dtype=np.float64)
    coupling = np.zeros((1, 1, 1), dtype=np.float64)

    for index in range(fe_ext_hz.size - 1):
        # Heun evalúa dfun en t_n y t_{n+1}; cada etapa recibe su entrada.
        inputs = iter(((fe_ext_hz[index], fi_ext_hz[index]),
                       (fe_ext_hz[index + 1], fi_ext_hz[index + 1])))

        def dfun(x, c, local_coupling):
            fe_hz, fi_hz = next(inputs)
            set_external_input(model, fe_hz, fi_hz)
            return model.dfun(x, c, local_coupling)

        state = integrator.scheme(state, dfun, coupling, 0.0, 0.0)
        state[0:2] = np.clip(state[0:2], 0.0, 5.0)
        state[2:4] = np.clip(state[2:4], -100000.0, 100000.0)
        state[4] = 0.0
        history[index + 1] = state[:, 0, 0]

    return history


def main() -> None:
    time_ms, stimulus_hz, fe_ext_hz, fi_ext_hz = build_pulse_input()
    history = integrate(build_model(), fe_ext_hz, fi_ext_hz)
    output_path = save_result(
        time_ms, stimulus_hz, fe_ext_hz, fi_ext_hz, history, OUTPUT_PATH
    )
    print(f"Resultado guardado en {output_path}")


if __name__ == "__main__":
    main()
