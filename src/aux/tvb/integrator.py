import numpy as np
from tvb.simulator import noise as Noise, integrators as Integrators


def get_integrator_class(integrator_name): return getattr(Integrators, integrator_name)


def get_noise_class(noise_name): return getattr(Noise, noise_name)


def build_integrator(dt_ms, integrator_class = "HeunDeterministic" ,noise_config=None):
    integrator = get_integrator_class(integrator_class)(dt = dt_ms)
    
    if noise_config is not None:
        noise_class = get_noise_class(noise_config.get("name", "Additive"))
        noise = noise_class()

        if "params" in noise_config:
            for name, value in noise_config["params"].items():
                if value is None: continue
                if isinstance(value, (list, tuple)):
                    value = np.array(value, dtype=np.float64)
                setattr(noise, name, value)

        integrator.noise = noise

    return integrator
