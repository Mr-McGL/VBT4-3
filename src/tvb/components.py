import numpy as np
from tvb.simulator.models import ModelsEnum
from tvb.simulator import noise as Noise, integrators as Integrators


def get_model_class(model_name): return ModelsEnum(model_name).get_class()


def get_integrator_class(integrator_name): return getattr(Integrators, integrator_name)


def get_noise_class(noise_name): return getattr(Noise, noise_name)


def build_model(parameters, integer_parameters, 
                model_class="ZerlautAdaptationFirstOrder",
                variable_of_interest=None):
    model = get_model_class(model_class)()

    for name, value in parameters.items():
        dtype = np.int64 if name in integer_parameters else np.float64
        setattr(model, name, np.array([value], dtype=dtype))

    # Esto se usa para el monitor Raw que se utiliza para guardar la salida de la simulación.
    # Por defecto solo se guarda E.
    if variable_of_interest is not None:
        if any(var not in model.state_variables for var in variable_of_interest):
            raise ValueError(f"Some variables of interest are not state variables: \n {variable_of_interest} \n {model.state_variables}")
        
        model.variables_of_interest = variable_of_interest
    
    return model


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
