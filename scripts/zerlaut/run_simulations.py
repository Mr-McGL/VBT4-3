from dotenv import dotenv_values, find_dotenv
from pathlib import Path
import os, sys

# Busqueda de ficheros dotenv
defaults_file = find_dotenv('.env_default', usecwd=True)

if not defaults_file:
    raise FileNotFoundError('Start Jupyter within the repository containing .env_default.')
env_dir = Path(defaults_file).resolve().parent

# Actualización de varaibles de entorno
settings = {**dotenv_values(defaults_file), **dotenv_values(env_dir / '.env')}
settings = {k: v if v is not None else '' for k, v in settings.items() }

os.environ.update(settings)

# Librerías auxiliares
import_dir = Path(settings.get('IMPORT_DIR') or env_dir).expanduser()
if not import_dir.is_absolute():
    import_dir = env_dir / import_dir
sys.path.insert(0, str(import_dir.resolve()))







from argparse import ArgumentParser
import json5 as json
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from time import perf_counter
from io import StringIO

import numpy as np
import logging

# from joblib import Parallel, delayed

from aux.parameters import flatten_params, restore_flat_params
from aux.sampling import sample_params
from aux.tvb.stimulus import build_stimulus
from aux.tvb.model import build_model, get_model_class
from aux.tvb.integrator import build_integrator
from aux.tvb.simulator import build_single_region_simulator

from rich.console import Console
pprint = Console(force_terminal=True, force_jupyter=False, width=140).print
pprint(f'The console is "ready" to print messages with rich formatting.')

# TODO: El sistema de log es mejorrable

def validate_config(config):
    errors = []
    if config.get("seed", 42) < 0:
        errors.append("seed must be non-negative")
    if config.get("batch_size", 32) <= 0:
        errors.append("batch_size must be positive")
    for name in ("duration_ms", "dt_ms"):
        if config["simulation"][name] <= 0:
            errors.append(f"simulation.{name} must be positive")

    for name, values in config["model"]["sampled_parameters"].items():
        lengths = {len(value) for value in values.values() if isinstance(value, list)}
        if lengths and (len(lengths) != 1 or 0 in lengths
                        or not all(isinstance(value, list) for value in values.values())):
            errors.append(f"{name}: vector fields must have the same length")
            continue
        for key, parameter in flatten_params({name: values}).items():
            minimum, maximum = parameter["min"], parameter["max"]
            if minimum > maximum:
                errors.append(f"{key}: min exceeds max")
            method = parameter.get("method", "uniform")
            if method not in ("uniform", "beta", "truncnorm"):
                errors.append(f"{key}: unknown sampling method '{method}'")
            elif method == "beta":
                if not minimum <= parameter["default"] <= maximum:
                    errors.append(f"{key}: beta default outside [min, max]")
                if parameter.get("lambda", -1) < 0:
                    errors.append(f"{key}: beta lambda must be non-negative")
            elif method == "truncnorm" and parameter.get("std", 0) <= 0:
                errors.append(f"{key}: truncnorm std must be positive")

    configurations = config["stimulus"]["configurations"]
    probabilities = np.asarray(config["stimulus"]["probabilities"])
    if not configurations or len(configurations) != len(probabilities):
        errors.append("stimulus: expected one probability per configuration")
    if np.any(probabilities < 0) or not np.isclose(probabilities.sum(), 1.0, rtol=0, atol=1e-8):
        errors.append("stimulus: probabilities must be non-negative and sum to one")

    if errors:
        raise ValueError("Invalid configuration:\n- " + "\n- ".join(errors))


INTEGER_PARAMETERS_BY_MODEL = {
    "ZerlautAdaptationFirstOrder": {"N_tot", "K_ext_e", "K_ext_i"},
    "ZerlautAdaptationSecondOrder": {"N_tot", "K_ext_e", "K_ext_i"},
}

NOISE_VARIABLES_BY_MODEL = {
    "ZerlautAdaptationFirstOrder": ["ou_drift"],
    "ZerlautAdaptationSecondOrder": ["ou_drift"],
}

# Parámetros de configuración de ruido para 
def build_noise_config(model_name):
    nsig = [0] * len(state_variables:=get_model_class(model_name).state_variables) 

    for var in NOISE_VARIABLES_BY_MODEL[model_name]:
        nsig[state_variables.index(var)] = 1

    return {"name": "Additive", "params": {"nsig": nsig}}


def simulate_trial(config, parameters, stimulus, n_steps):
    # 3.1 Config
    model_config, simulation_config = config["model"], config["simulation"]
    output_states = (output_config := config["output"])["states"]

    if output_states == "all":
        output_states = list(get_model_class(model_config["name"]).state_variables)

    # 3.2 Creación del modelo
    model = build_model(
        parameters, INTEGER_PARAMETERS_BY_MODEL[model_config["name"]],
        model_class=model_config["name"], variable_of_interest=output_states,
    )

    # 3.3 Creación del estímulo
    integrator = build_integrator(
        simulation_config["dt_ms"], integrator_class=simulation_config["integrator"],
        noise_config=build_noise_config(model_config["name"])
        if "Stochastic" in simulation_config["integrator"] else None,
    )

    # 3.4 Creación del simulador
    simulator = build_single_region_simulator(model, stimulus, integrator)
    time_ms, raw = simulator.run(n_steps=n_steps)[0]

    # 3.5 Resultados. Solo un modo y una región.
    states = {
        name: np.asarray(raw[:, index, 0, 0], dtype=output_config["dtype"])
        for index, name in enumerate(model.variables_of_interest)
    }
    
    return time_ms, states


def build_trial_stimulus(config, batch_id, trial_id, batch_seq_seed):
    # 2.1. Generación de semillas para la selección y generación de estímulos
    stimulus_selection_seed, stimulus_generation_seed = np.random.SeedSequence(
        batch_seq_seed, spawn_key=(batch_id, trial_id)
    ).spawn(2)

    stimulus_generation_seed = int(
        stimulus_generation_seed.generate_state(1, dtype=np.uint64)[0] 
    ) # debe ser un número para guardar el resultado.

    selection_rng = np.random.default_rng(stimulus_selection_seed) # se usa directamente como semilla

    # 2.2 Selección de un estímulo
    stim_conf = config["stimulus"]
    stimulus_index = int(selection_rng.choice(len(stim_conf["configurations"]), p=stim_conf["probabilities"]))
    stimulus_config = deepcopy(stim_conf["configurations"][stimulus_index])

    # 2.3 Generación del estímulo
    time_ms, stimulus = build_stimulus(
        stimulus_config, config["simulation"]["duration_ms"],
        config["simulation"]["dt_ms"], seed=stimulus_generation_seed,
    )

    # 2.4. Creación de metadatos del estímulo
    stimulus_metadata = {
        "stimulus": stimulus_config,
        "stimulus_seed": stimulus_generation_seed, 
        # "stimulus_probability": float(config["stimulus"]["probabilities"][stimulus_index]),
    }
    return time_ms, stimulus, stimulus_metadata


def save_config(config, output_dir):
    (output_dir := Path(output_dir)).mkdir(parents=True, exist_ok=True)

    # Comprueba si el fichero existe y si coicide con el de la carpeta de salida. Sino da error.
    file_path = output_dir / "config.json"
    if file_path.exists():
        if json.loads(file_path.read_text(encoding="utf-8")) != config:
            raise ValueError("Output folder configuration does not match config.json")
    else:
        file_path.write_text(json.dumps(config, indent=2, quote_keys=True, trailing_commas=False), encoding="utf-8")


# TODO: es una función distinta a la que usan los cuadernos 01a-01e. Lo ideal sería homogeneizar.  Problema
#     * **Ruido**, unidades
def save_single_region_simulation_(file_path, time_ms, states, metadata):
    file_path = Path(file_path)
    with file_path.with_suffix(".tmp").open("wb") as output:
        np.savez(output, time_ms=time_ms, **states, metadata_json=np.array(json.dumps(metadata)))
    file_path.with_suffix(".tmp").replace(file_path)


def simulate_batch(config, batch_id, sobol_seed, batch_seq_seed, output_dir):
    batch_size = config.get("batch_size", 32)
    sampled_parameters = flatten_params(config["model"]["sampled_parameters"])

    for trail_id, (parameters, probabilities) in enumerate(
        sample_params(
            sampled_parameters, n_samples=batch_size,
            fordware=batch_id * batch_size, seed=sobol_seed,
        )
    ):
        # 1. Parámetros de configuración
        parameters = restore_flat_params(parameters) | deepcopy(config["model"]["fixed_parameters"])
        simulation_id = batch_id * batch_size + trail_id
        file_path = output_dir / f"trial_{simulation_id:08d}.npz"
        if file_path.exists(): continue

        # 2. Generación de los estimulos
        time_ms, stimulus, stimulus_metadata = build_trial_stimulus(
            config, batch_id, trail_id, batch_seq_seed
        )

        ############################
        # S_i work arround. Es feo pero por ahora vale. 
        if config["model"]["name"] == "ZerlautAdaptationFirstOrder" and "S_i" in parameters:
            for i, (name, signal) in enumerate(stimulus):
                if name == "external_input_in_ex":
                    stimulus[i] =(name, signal * parameters["S_i"])
        ############################

        # 3. Simulation
        print(f"Simulating trial {simulation_id} (batch {batch_id}, trial {trail_id})...", flush=True) # LOG
        time_ms, states = simulate_trial(config, parameters, stimulus, len(time_ms))

        # 4. Almacenamiento de los resultados
        metadata = {
            "simulation_id": simulation_id, "batch_id": batch_id, "trial_id": trail_id,
            "parameters": parameters, "probability": float(np.prod(list(probabilities.values()))), 
            "probabilities": restore_flat_params(probabilities),
            **stimulus_metadata,
        }

        save_single_region_simulation_(file_path, time_ms, states, metadata)


def run_batch(config, batch_id, sobol_seed, batch_seq_seed, output_dir):
    started = perf_counter()
    output = StringIO()
    error = None

    # Salida de logging de TVB
    console = next(h for h in logging.getLogger("tvb.simulator").handlers 
                   if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler))
    tvb_out = console.stream
    console.setStream(output)    

    with redirect_stdout(output), redirect_stderr(output):
        try:
            simulate_batch(config, batch_id, sobol_seed, batch_seq_seed, Path(output_dir))
        except Exception as failure:
            error = failure
        finally:
            console.setStream(tvb_out)

    return {
        "batch_id": batch_id,
        "duration_s": perf_counter() - started,
        "logs": output.getvalue().splitlines(),
        "error": error,
    }

def run_batches(config, output_dir, *, first_batch=0, n_batches=None, n_workers=1):
    # Validación de la configuración
    validate_config(config)
    save_config(config, output_dir := Path(output_dir))

    # Finished batch log
    (completed_log_path := output_dir / "completed_batches.log").touch(exist_ok=True)
    completed = set(map(int, completed_log_path.read_text(encoding="utf-8").split()))

    # IO LOG
    (io_log_path := output_dir / "io.log").touch(exist_ok=True)

    # Seeds for Sobol sampling and batch sequence generation
    seed = config.get("seed", 42) #pop
    seeds = tuple(map( #sobol_seed, batch_seq_seed
        int, np.random.SeedSequence(seed).generate_state(2, dtype=np.uint64)
    ))

    # LOOP
    count, mean_duration_s = 0, 0.0
    started = perf_counter() 
    with (
            ProcessPoolExecutor(max_workers=n_workers) as pool, 
            completed_log_path.open("a", buffering=1, encoding="utf-8") as clog,
            io_log_path.open("a", buffering=1, encoding="utf-8") as iolog
        ):
       
        futures = {
            pool.submit(run_batch, config, batch, *seeds, output_dir)
            for batch in range(first_batch, first_batch + (1 if n_batches is None else n_batches))
            if batch not in completed  # ToDo: Mejorar el reanuadar.
        }
       
        for future in as_completed(futures):
            futures.remove(future) # TODO:Libera memoria, pero puede que no merezca la
            batch = future.result()
            iolog.write(f'Batch {batch["batch_id"]}: {batch["duration_s"]:.2f} s\n')
            iolog.write('\n'.join(batch["logs"]) + '\n\n\n')
            if batch["error"] is not None: raise batch["error"]
            
            clog.write(f'{batch["batch_id"]}\n')  
            
            mean_duration_s += (batch["duration_s"] - mean_duration_s) / (count:=count+1)
            pprint(f'Batch {batch["batch_id"]}: {batch["duration_s"]:.2f} s; mean: {mean_duration_s:.2f} s')
    stopped = perf_counter()
    pprint(f'All batches completed in {stopped - started:.2f} s')
    iolog.write(f'\n\nTotal time: {stopped - started:.2f} s\n')


if __name__ == "__main__":
    parser = ArgumentParser(description="Run simulation batches from a JSON configuration.")
    parser.add_argument("config_file", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--first-batch", type=int, default=0)
    parser.add_argument("--n-batches", type=int, default=None)
    parser.add_argument("--n-workers", type=int, default=1)
    args = parser.parse_args()

    with args.config_file.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    run_batches(config, args.output_dir,
                first_batch=args.first_batch, n_batches=args.n_batches, n_workers=args.n_workers)

    with (args.output_dir / "io.log").open("a", encoding="utf-8") as iolog:
        iolog.write(f"Total time: {perf_counter() - started:.2f} s\n")
