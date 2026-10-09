import numpy as np
from tvb.simulator.models import ModelsEnum


def get_model_class(model_name): return ModelsEnum(model_name).get_class()


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
