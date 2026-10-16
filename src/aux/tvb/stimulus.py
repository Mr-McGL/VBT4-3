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


def _validate_levels(points_ms, amplitudes_khz):
    points = np.asarray(points_ms, dtype=float)
    amplitudes = np.asarray(amplitudes_khz, dtype=float)

    if (points.ndim != 1 or amplitudes.ndim != 1 or len(points) == 0 or len(points) != len(amplitudes)):
        raise ValueError("points_ms and amplitudes_khz need matching, ordered finite values")

    return points, amplitudes

def _smoothstep(fraction):
    return fraction * fraction * (3.0 - 2.0 * fraction)


def _build_step(time_ms, baseline_khz, onset_ms, points_ms, amplitudes_khz):
    points, amplitudes = _validate_levels(points_ms, amplitudes_khz)

    signal = np.full(time_ms.shape, baseline_khz, dtype=float)

    # ToDo: Busacar algo más eficiente. Ahora se sobreescriben muchos valores.
    #       Mirar index = np.searchsorted
    for point, amplitude in zip(points, amplitudes):
        signal[time_ms >= onset_ms + point] = amplitude

    return signal


def _build_smooth(time_ms, baseline_khz, onset_ms, points_ms, amplitudes_khz):
    points, amplitudes = _validate_levels(points_ms, amplitudes_khz)

    # Permite transicionar suavemente desde el valor de referencia (baseline_khz) hasta el primer valor de amplitud.
    if points[0] > 0:
        points = np.r_[0.0, points]
        amplitudes = np.r_[baseline_khz, amplitudes]

    signal = np.full(time_ms.shape, baseline_khz, dtype=float)

    for start, end, a, b in zip(points[:-1], points[1:], amplitudes[:-1], amplitudes[1:]):
        t0, t1 = onset_ms + start, onset_ms + end
        mask = (time_ms >= t0) & (time_ms < t1)
        fraction = (time_ms[mask] - t0) / (t1 - t0)

        signal[mask] = a + (b - a) * _smoothstep(fraction)

    signal[time_ms >= onset_ms + points[-1]] = amplitudes[-1]

    return signal


def _random_stimulation(time_ms, onset_ms, min_duration_ms, max_duration_ms,
                        min_amplitude_khz, max_amplitude_khz, rng):

    if (min_duration_ms <= 0 or max_duration_ms < min_duration_ms
            or max_amplitude_khz < min_amplitude_khz):
        raise ValueError("Invalid duration or amplitude range")

    points_ms = []
    amplitudes_khz = []
    elapsed_ms = 0.0

    while onset_ms + elapsed_ms <= time_ms[-1]:
        elapsed_ms += rng.uniform(min_duration_ms, max_duration_ms)
        points_ms.append(elapsed_ms)
        amplitudes_khz.append(rng.uniform(min_amplitude_khz, max_amplitude_khz))

    return points_ms, amplitudes_khz


def _build_random_step(time_ms, baseline_khz, onset_ms, min_duration_ms,
                       max_duration_ms, min_amplitude_khz, max_amplitude_khz, rng):
    points, amplitudes = _random_stimulation(
        time_ms, onset_ms, min_duration_ms, max_duration_ms,
        min_amplitude_khz, max_amplitude_khz, rng
    )

    return _build_step(time_ms, baseline_khz, onset_ms,
                       [0.0, *points[:-1]], amplitudes)


def _build_random_smooth(time_ms, baseline_khz, onset_ms, min_duration_ms,
                         max_duration_ms, min_amplitude_khz, max_amplitude_khz,
                         rng):
    points, amplitudes = _random_stimulation(
        time_ms, onset_ms, min_duration_ms, max_duration_ms,
        min_amplitude_khz, max_amplitude_khz, rng
    )

    return _build_smooth(time_ms, baseline_khz, onset_ms, points, amplitudes)


def _build_additive_noise(time_ms, mean_khz, std_khz, rng):
    return rng.normal(mean_khz, std_khz, time_ms.shape)


def _build_random_std_noise(time_ms, mean_khz, min_std_khz, max_std_khz, rng):
    if min_std_khz < 0 or max_std_khz < min_std_khz:
        raise ValueError("Invalid standard deviation range")
    std_khz = rng.uniform(min_std_khz, max_std_khz, time_ms.shape)
    return rng.normal(mean_khz, std_khz)


STIMULUS_BUILDERS = {
    "pulse": _build_pulse,
    "pulse_train": _build_pulse_train,
    "step": _build_step,
    "smooth": _build_smooth,
    "random_step": _build_random_step,
    "random_smooth": _build_random_smooth,
    "additive_noise": _build_additive_noise,
    "random_std_noise": _build_random_std_noise,
}

RANDOM_BUILDERS = {"random_step", "random_smooth",
                   "additive_noise", "random_std_noise"}


def build_stimulus(stimulus, duration_ms, dt_ms, seed=None):
    time_ms = np.arange(0.0, duration_ms, dt_ms)
    rng = np.random.default_rng(seed)
    output = {}


    # ToDo: Por ahora solo se permite una señal de un tipo.
    #       Crear tipos de estímulos que permitan combinaciones.
    for key, value in stimulus.items():
        if value is None: continue

        # Es un diccionario con un solo elemento, que indica el tipo de estímulo y sus parámetros.
        # ToDo: Permitir multiples elementos.
        for kind, parameters in value.items():
            if kind in STIMULUS_BUILDERS:
                builder = STIMULUS_BUILDERS[kind]
                if not isinstance(parameters, list): parameters = [parameters]
                for signal_parameters in parameters:
                    if kind in RANDOM_BUILDERS:
                        signal = builder(time_ms, rng=rng, **signal_parameters)
                    else:
                        signal = builder(time_ms, **signal_parameters)
                    output[key] = output.get(key, 0) + signal


    for key, value in stimulus.items():
        if value is None: continue

        # Ya sabemos que es un diccionario de un solo elemento.
        for source, scale in value.items():
            if source in stimulus:
                if source not in output:
                    raise ValueError(
                        f"Stimulus value for {key} requires '{source}' to be defined."
                    )

                output[key] = output.get(key, 0) + scale * output[source]

    return time_ms, [(key, output[key][:, np.newaxis]) for key in output]
