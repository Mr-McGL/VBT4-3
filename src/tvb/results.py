import json5 as json
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np


@dataclass
class SimulationMetadata:
    duration_ms: float
    dt_ms: float
    integrator: str = "HeunDeterministic"
    output_dtype: str = "float32"
    noise_type: str = "Additive"
    noise_params: dict = None
    
    def __post_init__(self):
        if not isinstance(self.integrator, str):
            self.integrator = type(self.integrator).__name__


@dataclass
class ModelMetadata:
    name: str = "ZerlautAdaptationFirstOrder"
    parameters: dict[str, float | int] = None
    integer_parameters: list[str] = None
    output_variables: list[str] = None
    state_units: dict[str, str] = None
    stimulus_units: dict[str, str] = None
        
    def __post_init__(self):
        if not isinstance(self.name, str):
            self.name = type(self.name).__name__


@dataclass
class ResultMetadata:
    simulation: SimulationMetadata
    model: ModelMetadata
    stimulus: dict


def save_single_region_simulation(
    file_path, time_ms, simulation_output, metadata,
):
    output_variables = metadata.model.output_variables

    # ToDo: Faltan muchas comprobaciones.
    if len(output_variables) != simulation_output.shape[1]:
        raise ValueError("Output variables do not match simulation output shape")

    result = {"time_ms": time_ms}
    result.update(
        {
            var: np.asarray(simulation_output[:, i], dtype=metadata.simulation.output_dtype) 
            for i, var in enumerate(output_variables)
        }
    )

    (file_path := Path(file_path)).parent.mkdir(parents=True, exist_ok=True)
    
    np.savez(
        file_path, **result,
        metadata_json=np.array(json.dumps(asdict(metadata))),
    )


def load_results(path):
    with np.load(path, allow_pickle=False) as saved:
        data = json.loads(saved["metadata_json"].item())
        metadata = ResultMetadata(
            simulation=SimulationMetadata(**data["simulation"]),
            model=ModelMetadata(**data["model"]),
            stimulus=data["stimulus"],
        )
        times = np.asarray(saved["time_ms"], dtype=float)
        states = {
            name: np.asarray(saved[name], dtype=float)
            for name in metadata.model.output_variables
        }

    return {"time_ms": times, "states": states, "metadata": metadata}
