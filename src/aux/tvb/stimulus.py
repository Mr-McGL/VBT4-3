import numpy as np


def _build_pulse(
        time_ms, baseline_khz, pulse_amplitude_khz, pulse_onset_ms, pulse_duration_ms
):
    stimulus = np.full(time_ms.shape, baseline_khz)
    pulse_mask = ((time_ms >= pulse_onset_ms) & 
        (time_ms < pulse_onset_ms + pulse_duration_ms))
    stimulus[pulse_mask] = pulse_amplitude_khz
    
    return stimulus


def _build_pulse_train(
        time_ms, baseline_khz, pulse_amplitude_khz, pulse_onset_ms,
        pulse_duration_ms, pulse_period_ms,
):
    stimulus = np.full(time_ms.shape, baseline_khz)
    phase_ms = (time_ms - pulse_onset_ms) % pulse_period_ms
    pulse_mask = ((time_ms >= pulse_onset_ms) & 
        (phase_ms < pulse_duration_ms))
    stimulus[pulse_mask] = pulse_amplitude_khz

    return stimulus


def build_stimulus(stimulus, duration_ms, dt_ms):
    time_ms = np.arange(0.0, duration_ms, dt_ms)
    output = {}
    for key, value in stimulus.items():
        if value is None: 
            continue

        # ToDo: Por ahora solo se permite una señal de un tipo. 
        #       Crear tipos de estímulos que permitan combinaciones.
        if not isinstance(value, dict) or len(value) != 1:
            raise ValueError(f"Stimulus value for {key} must be a dictionary with one key.")

        match next(iter(value.keys())): # Solo hay una clave en el diccionario.
            case "pulse_train":
                output[key] = _build_pulse_train(time_ms, **value["pulse_train"])
            case "pulse":
                output[key] = _build_pulse(time_ms, **value["pulse"])
        
        # ToDo: Otros tipos de estímulos ...

    for key, value in stimulus.items():
        if value is None:
            continue

        # Ya sabemos que es un diccionario de un solo elemento.
        source, scale = next(iter(value.items())) 

        if source in stimulus:
            if source not in output:
                raise ValueError(
                    f"Stimulus value for {key} requires '{source}' to be defined."
                )

            output[key] = scale * output[source]

    return time_ms, [(key, output[key][:, np.newaxis]) for key in output]
