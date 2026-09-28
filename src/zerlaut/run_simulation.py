#!/usr/bin/env python3
"""Run a one-region TVB Zerlaut simulation configured by JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from tvb.simulator.models.zerlaut import ZerlautAdaptationFirstOrder


INTEGER_PARAMETERS = {"N_tot", "K_ext_e", "K_ext_i"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulación TVB Zerlaut-AdEx de una única región."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/simulation.json"),
        help="Fichero JSON de configuración.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Sobrescribe output.path del JSON.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    """Load the JSON configuration."""
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def make_stimulus(time_ms: np.ndarray, config: Mapping[str, Any]) -> np.ndarray:
    """Build one of the reference project's deterministic stimulus protocols."""
    kind = str(config["type"]).lower()
    baseline = float(config["baseline_hz"])
    amplitude = float(config["amplitude_hz"])
    onset = float(config.get("onset_ms", 0.0))
    duration = float(config.get("duration_ms", time_ms[-1] - onset))
    stimulus = np.full(time_ms.shape, baseline, dtype=np.float64)
    active = (time_ms >= onset) & (time_ms < onset + duration)

    if kind == "constant":
        stimulus += amplitude
    elif kind == "step":
        stimulus[time_ms >= onset] += amplitude
    elif kind == "pulse":
        stimulus[active] += amplitude
    elif kind == "slow_ramp":
        ramp = np.clip((time_ms - onset) / duration, 0.0, 1.0)
        stimulus += amplitude * ramp
    elif kind in {"double_pulse", "recovery"}:
        gap = float(config.get("inter_pulse_interval_ms", duration))
        second_amplitude = float(config.get("second_amplitude_hz", amplitude))
        second_onset = onset + duration + gap
        second_active = (time_ms >= second_onset) & (time_ms < second_onset + duration)
        stimulus[active] += amplitude
        stimulus[second_active] += second_amplitude
    elif kind == "sine":
        frequency = float(config.get("frequency_hz", 1.0))
        phase = float(config.get("phase_rad", 0.0))
        seconds = time_ms * 1.0e-3
        stimulus += 0.5 * amplitude * (
            1.0 + np.sin(2.0 * np.pi * frequency * seconds + phase)
        )
    elif kind == "ou_like":
        tau = float(config.get("ou_tau_ms", 50.0))
        sigma = float(config.get("ou_sigma_hz", 5.0))
        seed = int(config.get("seed", 0))
        rng = np.random.default_rng(seed)
        target = baseline + amplitude
        stimulus[0] = target
        dt = float(time_ms[1] - time_ms[0])
        noise_scale = sigma * np.sqrt(2.0 * dt / tau)
        for index in range(time_ms.size - 1):
            drift = (target - stimulus[index]) * dt / tau
            stimulus[index + 1] = stimulus[index] + drift + noise_scale * rng.normal()

    return np.clip(stimulus, 0.0, None)


def configure_model(parameters: Mapping[str, Any]) -> ZerlautAdaptationFirstOrder:
    """Instantiate the TVB model with the parameter values from JSON."""
    model = ZerlautAdaptationFirstOrder()
    for name, raw_value in parameters.items():
        dtype = np.int64 if name in INTEGER_PARAMETERS else np.float64
        setattr(model, name, np.array([raw_value], dtype=dtype))
    model.weight_noise = np.array([0.0], dtype=np.float64)
    model.configure()
    return model


def _set_external_drive(
    model: ZerlautAdaptationFirstOrder, fe_hz: float, fi_hz: float
) -> None:
    """Apply the same E/I external drives to both target populations."""
    fe_khz = np.array([fe_hz * 1.0e-3], dtype=np.float64)
    fi_khz = np.array([fi_hz * 1.0e-3], dtype=np.float64)
    model.external_input_ex_ex = fe_khz
    model.external_input_in_ex = fe_khz.copy()
    model.external_input_ex_in = fi_khz
    model.external_input_in_in = fi_khz.copy()


def run_simulation(config: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """Integrate the TVB model for one uncoupled region with Euler or Heun."""
    simulation = config["simulation"]
    duration_ms = float(simulation["duration_ms"])
    dt_ms = float(simulation["dt_ms"])
    method = str(simulation["method"]).lower()
    time_ms = np.arange(0.0, duration_ms, dt_ms, dtype=np.float64)

    stimulus_hz = make_stimulus(time_ms, config["stimulus"])
    scale = float(config["external_drive"]["scale"])
    fi_ratio = float(config["external_drive"]["Fi_ratio"])
    fe_ext_hz = scale * stimulus_hz
    fi_ext_hz = fi_ratio * fe_ext_hz

    model = configure_model(config["model"]["parameters"])
    initial = simulation.get("initial_state", {})
    state = np.zeros((5, 1, 1), dtype=np.float64)
    state[0, 0, 0] = float(initial.get("E_hz", 0.0)) * 1.0e-3
    state[1, 0, 0] = float(initial.get("I_hz", 0.0)) * 1.0e-3
    state[2, 0, 0] = float(initial.get("W_e_pA", 0.0))
    state[3, 0, 0] = float(initial.get("W_i_pA", 0.0))
    coupling = np.zeros((1, 1, 1), dtype=np.float64)

    history = np.empty((time_ms.size, 5), dtype=np.float64)
    history[0] = state[:, 0, 0]
    for index in range(time_ms.size - 1):
        _set_external_drive(model, fe_ext_hz[index], fi_ext_hz[index])
        derivative_0 = model.dfun(state, coupling)
        if method == "euler":
            next_state = state + dt_ms * derivative_0
        else:
            predicted = state + dt_ms * derivative_0
            _set_external_drive(model, fe_ext_hz[index + 1], fi_ext_hz[index + 1])
            derivative_1 = model.dfun(predicted, coupling)
            next_state = state + 0.5 * dt_ms * (derivative_0 + derivative_1)

        next_state[0:2] = np.clip(next_state[0:2], 0.0, 5.0)
        next_state[2:4] = np.clip(next_state[2:4], -1.0e5, 1.0e5)
        next_state[4] = 0.0
        state = next_state
        history[index + 1] = state[:, 0, 0]

    return {
        "time_ms": time_ms,
        "E_hz": history[:, 0] * 1.0e3,
        "I_hz": history[:, 1] * 1.0e3,
        "W_e_pA": history[:, 2],
        "W_i_pA": history[:, 3],
        "stimulus_hz": stimulus_hz,
        "Fe_ext_hz": fe_ext_hz,
        "Fi_ext_hz": fi_ext_hz,
    }


def save_result(
    result: Mapping[str, np.ndarray],
    config: Mapping[str, Any],
    output_path: Path,
) -> None:
    """Save one complete experiment in its own NPZ file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dtype = np.dtype(config["output"]["dtype"])
    metadata = {"config": config}
    arrays = {name: np.asarray(values, dtype=dtype) for name, values in result.items()}
    np.savez(
        output_path,
        **arrays,
        metadata_json=np.array(json.dumps(metadata)),
    )


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    base_path = args.output if args.output is not None else Path(config["output"]["path"])
    run = config["simulation"]["run"]
    output_path = base_path.with_name(f"{base_path.stem}_run_{run}{base_path.suffix}")
    result = run_simulation(config)
    save_result(result, config, output_path)
    print(f"Run {run} guardada en {output_path}")
    print(
        f"Pasos: {result['time_ms'].size}; "
        f"E máx: {np.max(result['E_hz']):.3f} Hz; "
        f"I máx: {np.max(result['I_hz']):.3f} Hz"
    )


if __name__ == "__main__":
    main()
