#!/usr/bin/env python3
"""Minimal one-region Zerlaut simulation with every input hardcoded."""

import json
from pathlib import Path

import numpy as np
from tvb.simulator.models.zerlaut import ZerlautAdaptationFirstOrder


# 1) Entradas de la simulación.

# 1.0) Salida de la simulación.
OUTPUT_PATH = Path("results/simple_simulation.npz")
OUTPUT_DTYPE = "float32"


## 1.1) Parámetros de la simulación.
DURATION_MS = 2000.0    # Duración de la simulación en milisegundos.
DT_MS = 0.5             # Paso de integración en milisegundos.

## 1.2) Parámetros de la entrada. En este caso un pulso.
BASELINE_HZ = 5.0           # Frecuencia de disparo basal en Hz. Que hace esto? --
PULSE_AMPLITUDE_HZ = 40.0   # Amplitud del pulso en Hz.
PULSE_ONSET_MS = 500.0      # Instante de inicio del pulso en ms.
PULSE_DURATION_MS = 700.0   # Duración del pulso en ms.
INPUT_SCALE = 1.0           # Escala de la entrada externa. Que hace esto? --
FI_RATIO = 0.5              # Relación entre la entrada externa inhibitoria y la excitatoria

# 1.3) Parámetros del modelo Zerlaut-AdEx.
MODEL_PARAMETERS = {
    "g_L": 10.0,
    "C_m": 200.0,
    "E_L_e": -60.0,
    "E_L_i": -65.0,
    "a_e": 4.0,
    "b_e": 60.0,
    "tau_w_e": 200.0,
    "a_i": 0.0,
    "b_i": 20.0,
    "tau_w_i": 100.0,
    "E_e": 0.0,
    "E_i": -80.0,
    "Q_e": 1.0,
    "Q_i": 5.0,
    "tau_e": 5.0,
    "tau_i": 5.0,
    "N_tot": 10000,
    "p_connect_e": 0.05,
    "p_connect_i": 0.05,
    "g": 0.2,
    "K_ext_e": 400,
    "K_ext_i": 35,
    "T": 10.0,
}

# Todos los parámetros son de tipo float menos lo que están en esta lista. 
INTEGER_PARAMETERS = {"N_tot", "K_ext_e", "K_ext_i"}

def build_pulse_input() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create time, a pulse, and the E/I external firing rates in Hz."""
    
    time_ms = np.arange(0.0, DURATION_MS, DT_MS)
    stimulus_hz = np.full(time_ms.shape, BASELINE_HZ)

    pulse = (time_ms >= PULSE_ONSET_MS) & (
        time_ms < PULSE_ONSET_MS + PULSE_DURATION_MS)
    stimulus_hz[pulse] += PULSE_AMPLITUDE_HZ

    # Misma convención que el código de referencia.
    fe_ext_hz = INPUT_SCALE * stimulus_hz
    fi_ext_hz = FI_RATIO * fe_ext_hz
    return time_ms, stimulus_hz, fe_ext_hz, fi_ext_hz


def build_model() -> ZerlautAdaptationFirstOrder:
    """Create and configure TVB's first-order Zerlaut model."""
    model = ZerlautAdaptationFirstOrder()
    
    for name, value in MODEL_PARAMETERS.items():
        dtype = np.int64 if name in INTEGER_PARAMETERS else np.float64
        setattr(model, name, np.array([value], dtype=dtype))

    # Se desactiva el ruido interno para que el ejemplo sea reproducible.
    model.weight_noise = np.array([0.0])
    model.configure()
    return model


def set_external_input(
    model: ZerlautAdaptationFirstOrder, fe_hz: float, fi_hz: float
) -> None:
    """Put one time sample into TVB; TVB represents firing rates in kHz."""
    fe_khz = np.array([fe_hz / 1000.0])
    fi_khz = np.array([fi_hz / 1000.0])

    # Entradas E/I para las poblaciones excitatoria e inhibitoria.
    model.external_input_ex_ex = fe_khz.copy()
    model.external_input_in_ex = fe_khz.copy()
    model.external_input_ex_in = fi_khz.copy()
    model.external_input_in_in = fi_khz.copy()


def integrate(
    model: ZerlautAdaptationFirstOrder,
    fe_ext_hz: np.ndarray,
    fi_ext_hz: np.ndarray,
) -> np.ndarray:
    """Integrate one uncoupled region using the two-stage Heun method."""
    # E, I, W_e, W_i y deriva OU; una región y un modo.
    state = np.zeros((5, 1, 1), dtype=np.float64)
    history = np.zeros((fe_ext_hz.size, 5), dtype=np.float64)

    # No hay conectoma: el acoplamiento de esta única región es exactamente cero.
    coupling = np.zeros((1, 1, 1), dtype=np.float64)

    for index in range(fe_ext_hz.size - 1):
        set_external_input(model, fe_ext_hz[index], fi_ext_hz[index])
        slope_1 = model.dfun(state, coupling)

        predicted_state = state + DT_MS * slope_1
        set_external_input(model, fe_ext_hz[index + 1], fi_ext_hz[index + 1])
        slope_2 = model.dfun(predicted_state, coupling)

        state = state + 0.5 * DT_MS * (slope_1 + slope_2)
        state[0:2] = np.clip(state[0:2], 0.0, 5.0)
        state[2:4] = np.clip(state[2:4], -100000.0, 100000.0)
        state[4] = 0.0
        history[index + 1] = state[:, 0, 0]

    return history


def save_result(
    time_ms: np.ndarray,
    stimulus_hz: np.ndarray,
    fe_ext_hz: np.ndarray,
    fi_ext_hz: np.ndarray,
    history: np.ndarray,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Save one complete experiment in its own NPZ file."""
    result = {
        "time_ms": time_ms,
        "E_hz": history[:, 0] * 1000.0,
        "I_hz": history[:, 1] * 1000.0,
        "W_e_pA": history[:, 2],
        "W_i_pA": history[:, 3],
        "stimulus_hz": stimulus_hz,
        "Fe_ext_hz": fe_ext_hz,
        "Fi_ext_hz": fi_ext_hz,
    }
    config = {
        "simulation": {
            "duration_ms": DURATION_MS,
            "dt_ms": DT_MS,
            "method": "heun",
            "initial_state": {
                "E_hz": 0.0,
                "I_hz": 0.0,
                "W_e_pA": 0.0,
                "W_i_pA": 0.0,
            },
        },
        "model": {
            "name": "ZerlautAdaptationFirstOrder",
            "parameters": MODEL_PARAMETERS,
        },
        "external_drive": {
            "scale": INPUT_SCALE,
            "Fi_ratio": FI_RATIO,
        },
        "stimulus": {
            "type": "pulse",
            "baseline_hz": BASELINE_HZ,
            "amplitude_hz": PULSE_AMPLITUDE_HZ,
            "onset_ms": PULSE_ONSET_MS,
            "duration_ms": PULSE_DURATION_MS,
        },
        "output": {
            "path": str(output_path),
            "dtype": OUTPUT_DTYPE,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"config": config}
    arrays = {
        name: np.asarray(values, dtype=OUTPUT_DTYPE) for name, values in result.items()
    }
    np.savez(
        output_path,
        **arrays,
        metadata_json=np.array(json.dumps(metadata)),
    )
    return output_path


def main() -> None:
    time_ms, stimulus_hz, fe_ext_hz, fi_ext_hz = build_pulse_input()
    history = integrate(build_model(), fe_ext_hz, fi_ext_hz)

    # TVB calcula E e I en kHz; save_result las convierte a Hz al guardarlas.
    output_path = save_result(time_ms, stimulus_hz, fe_ext_hz, fi_ext_hz, history)
    print(f"Resultado guardado en {output_path}")
    print(f"No se ha leído ningún fichero de conectividad ni de datos.")


if __name__ == "__main__":
    main()
