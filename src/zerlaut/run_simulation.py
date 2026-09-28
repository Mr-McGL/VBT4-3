#!/usr/bin/env python3
"""Run a one-region TVB Zerlaut simulation configured by JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from tvb.simulator.models.zerlaut import ZerlautAdaptationFirstOrder


SUPPORTED_STIMULI = {
    "constant",
    "step",
    "pulse",
    "slow_ramp",
    "double_pulse",
    "recovery",
    "sine",
    "ou_like",
}

MODEL_PARAMETERS = {
    "g_L",
    "C_m",
    "E_L_e",
    "E_L_i",
    "a_e",
    "b_e",
    "tau_w_e",
    "a_i",
    "b_i",
    "tau_w_i",
    "E_e",
    "E_i",
    "Q_e",
    "Q_i",
    "tau_e",
    "tau_i",
    "N_tot",
    "p_connect_e",
    "p_connect_i",
    "g",
    "K_ext_e",
    "K_ext_i",
    "T",
}

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
    """Load a JSON object and report malformed input clearly."""
    try:
        with path.open("r", encoding="utf-8") as stream:
            config = json.load(stream)
    except FileNotFoundError as exc:
        raise ValueError(f"No existe el fichero de configuración: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON no válido en {path}: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("La raíz de la configuración debe ser un objeto JSON.")
    return config


def _number(section: Mapping[str, Any], key: str, *, minimum: float | None = None) -> float:
    if key not in section or isinstance(section[key], bool):
        raise ValueError(f"Falta un valor numérico para '{key}'.")
    try:
        value = float(section[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{key}' debe ser numérico.") from exc
    if not np.isfinite(value):
        raise ValueError(f"'{key}' debe ser finito.")
    if minimum is not None and value < minimum:
        raise ValueError(f"'{key}' debe ser mayor o igual que {minimum}.")
    return value


def validate_config(config: Mapping[str, Any]) -> None:
    """Validate the fields that determine simulation shape and semantics."""
    required = {"simulation", "model", "external_drive", "stimulus", "output"}
    missing = sorted(required.difference(config))
    if missing:
        raise ValueError(f"Faltan secciones en el JSON: {missing}")

    simulation = config["simulation"]
    model = config["model"]
    drive = config["external_drive"]
    stimulus = config["stimulus"]
    output = config["output"]
    if not all(isinstance(x, Mapping) for x in (simulation, model, drive, stimulus, output)):
        raise ValueError("Las secciones principales deben ser objetos JSON.")

    duration = _number(simulation, "duration_ms", minimum=0.0)
    dt = _number(simulation, "dt_ms", minimum=0.0)
    if duration <= 0.0 or dt <= 0.0 or duration < 2.0 * dt:
        raise ValueError("duration_ms debe incluir al menos dos pasos dt_ms positivos.")
    if str(simulation.get("method", "")).lower() not in {"euler", "heun"}:
        raise ValueError("simulation.method debe ser 'euler' o 'heun'.")

    if model.get("name") != "ZerlautAdaptationFirstOrder":
        raise ValueError("Este ejemplo sólo admite ZerlautAdaptationFirstOrder.")
    parameters = model.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("model.parameters debe ser un objeto JSON.")
    unknown = sorted(set(parameters).difference(MODEL_PARAMETERS))
    if unknown:
        raise ValueError(f"Parámetros de modelo no admitidos: {unknown}")
    for name, value in parameters.items():
        _number(parameters, name)
        if name in INTEGER_PARAMETERS and int(value) != float(value):
            raise ValueError(f"'{name}' debe ser entero.")

    _number(drive, "scale", minimum=0.0)
    _number(drive, "Fi_ratio", minimum=0.0)
    stimulus_type = str(stimulus.get("type", "")).lower()
    if stimulus_type not in SUPPORTED_STIMULI:
        raise ValueError(
            f"Tipo de estímulo '{stimulus_type}' no admitido; use {sorted(SUPPORTED_STIMULI)}."
        )
    for key in ("baseline_hz", "amplitude_hz"):
        _number(stimulus, key, minimum=0.0)
    if output.get("dtype") not in {"float32", "float64"}:
        raise ValueError("output.dtype debe ser 'float32' o 'float64'.")
    if not isinstance(output.get("path"), str) or not output["path"].strip():
        raise ValueError("output.path debe ser una ruta no vacía.")


def make_stimulus(time_ms: np.ndarray, config: Mapping[str, Any]) -> np.ndarray:
    """Build one of the reference project's deterministic stimulus protocols."""
    kind = str(config["type"]).lower()
    baseline = _number(config, "baseline_hz", minimum=0.0)
    amplitude = _number(config, "amplitude_hz", minimum=0.0)
    onset = float(config.get("onset_ms", 0.0))
    duration = float(config.get("duration_ms", time_ms[-1] - onset))
    if onset < 0.0 or duration <= 0.0:
        raise ValueError("stimulus.onset_ms debe ser no negativo y duration_ms positivo.")

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
        if gap < 0.0 or second_amplitude < 0.0:
            raise ValueError("El intervalo y la segunda amplitud deben ser no negativos.")
        second_onset = onset + duration + gap
        second_active = (time_ms >= second_onset) & (time_ms < second_onset + duration)
        stimulus[active] += amplitude
        stimulus[second_active] += second_amplitude
    elif kind == "sine":
        frequency = float(config.get("frequency_hz", 1.0))
        phase = float(config.get("phase_rad", 0.0))
        if frequency <= 0.0:
            raise ValueError("stimulus.frequency_hz debe ser positivo.")
        seconds = time_ms * 1.0e-3
        stimulus += 0.5 * amplitude * (
            1.0 + np.sin(2.0 * np.pi * frequency * seconds + phase)
        )
    elif kind == "ou_like":
        tau = float(config.get("ou_tau_ms", 50.0))
        sigma = float(config.get("ou_sigma_hz", 5.0))
        seed = int(config.get("seed", 0))
        if tau <= 0.0 or sigma < 0.0:
            raise ValueError("ou_tau_ms debe ser positivo y ou_sigma_hz no negativo.")
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
        if not np.all(np.isfinite(next_state)):
            raise RuntimeError(
                f"La integración produjo valores no finitos en t={time_ms[index + 1]} ms."
            )
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
    """Save plain arrays plus JSON metadata in an unpickled NPZ container."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dtype = np.dtype(config["output"]["dtype"])
    arrays = {name: np.asarray(values, dtype=dtype) for name, values in result.items()}
    metadata = {
        "format": "tvb-single-region-npz-v1",
        "model": config["model"]["name"],
        "region_count": 1,
        "units": {
            "time_ms": "ms",
            "E_hz": "Hz",
            "I_hz": "Hz",
            "W_e_pA": "pA",
            "W_i_pA": "pA",
            "stimulus_hz": "Hz",
            "Fe_ext_hz": "Hz",
            "Fi_ext_hz": "Hz",
        },
        "config": config,
    }
    np.savez(output_path, **arrays, metadata_json=np.array(json.dumps(metadata)))


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    validate_config(config)
    output_path = args.output if args.output is not None else Path(config["output"]["path"])
    result = run_simulation(config)
    save_result(result, config, output_path)
    print(f"Resultado guardado en {output_path}")
    print(
        f"Pasos: {result['time_ms'].size}; "
        f"E máx: {np.max(result['E_hz']):.3f} Hz; "
        f"I máx: {np.max(result['I_hz']):.3f} Hz"
    )


if __name__ == "__main__":
    main()
