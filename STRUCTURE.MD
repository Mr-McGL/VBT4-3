# Project structure

## Purpose

This file describes the current repository layout. Read it before creating,
moving, modifying, or deleting project files. Update it whenever those changes
make the layout or responsibilities below inaccurate.

## Current tree

```text
tvb_test/
├── AGENTS.MD
├── README.md
├── STRUCTURE.MD
├── VBT_4-3.MD
├── .gitignore
├── .env_default               # Tracked directory defaults
├── .env                       # Ignored local directory overrides
├── .prompts/                  # User-reserved area; agents must not access it
├── .vscode/                   # Editor settings
├── 0.sample_code/             # External reference code; read-only
├── conda/
│   └── environment.yml        # Micromamba environment
├── config/
│   └── zerlaut/
│       └── params_raw.json     # Zerlaut parameter data
├── notebooks/
│   └── zerlaut/
│       ├── 01a_simulation_one_region.ipynb
│       ├── 01b_simulation_one_region.ipynb
│       ├── 01c_simulation_one_region.ipynb
│       ├── 01d_simulation_two_regions.ipynb
│       ├── 01e_simulation_one_region.ipynb
│       ├── 02_sampling_test.ipynb
│       ├── 03_parameter_exploration.ipynb
│       ├── 04_configuration_files.ipynb
│       ├── 05_plot_simulations.ipynb
│       ├── 06_interactive_plot_simulations.ipynb
│       └── 99a_simulation_configuration.ipynb
├── scripts/                   # Future executable scripts: <topic>/<name>.py
├── src/                       # Directly imported helpers; no build metadata
│   └── aux/
│       ├── __init__.py
│       ├── environment.py      # Resolve working and results directories
│       ├── parameters.py       # Parameter reshaping and sampling configuration
│       ├── sampling.py         # Sobol and distribution sampling helpers
│       └── tvb/
│           ├── __init__.py
│           ├── stimulus.py     # Composable stimulus arrays and noise
│           ├── model.py        # Model builder
│           ├── integrator.py   # Integrator and noise builder
│           ├── simulator.py    # Dynamic parameters and single-region simulator
│           ├── results.py      # Result metadata and NPZ persistence
│           └── plotting.py     # Result plots
└── results/                   # Generated NPZ files; ignored by Git
```

## Responsibilities and relationships

- `AGENTS.MD` contains mandatory repository instructions for agents.
- `README.md` explains how to prepare the environment and run the notebooks.
- `VBT_4-3.MD` indexes the external reference code in `0.sample_code/sinovia`.
- `0.sample_code/` is external reference material and must not be modified.
- `.prompts/` is reserved for the user and must not be accessed by agents.
- `.env_default` contains tracked path defaults, including `IMPORT_DIR` for the directory containing `src/`. The ignored `.env` may override them locally. Neither file contains simulation or model values.
- `conda/environment.yml` defines the Python environment, including `python-dotenv`, `json5`, `joblib`, and TVB.
- `config/zerlaut/params_raw.json` stores Zerlaut parameter data.
- `notebooks/zerlaut/01a_simulation_one_region.ipynb` is the original single-region teaching example.
- `notebooks/zerlaut/01b_simulation_one_region.ipynb` uses the helpers in `src/aux/` for single-region simulations.
- `notebooks/zerlaut/01c_simulation_one_region.ipynb` compares external stimulation signals using the shared builders.
- `notebooks/zerlaut/01d_simulation_two_regions.ipynb` explores signal tracking and directed coupling.
- `notebooks/zerlaut/01e_simulation_one_region.ipynb` compares `weight_noise` and `tau_OU` under a constant baseline input.
- `notebooks/zerlaut/03_parameter_exploration.ipynb` groups Zerlaut defaults, counts parameters, explores ranges, and runs simulation grids for each parameter group. Its additional `ou_drift` analysis belongs only to Noise.
- `notebooks/zerlaut/02_sampling_test.ipynb` and `99a_simulation_configuration.ipynb` contain additional Zerlaut experiments.
- `notebooks/zerlaut/04_configuration_files.ipynb` defines model sampling and stimulus configurations, and simulates batches from consecutive blocks of a global Sobol sequence. The notebook validates configuration before drawing random numbers and extracts stimulus selection and generation into `build_trial_stimulus`. Each trial has independent stimulus selection and generation streams. Its metadata contains parameters, their sampling densities, the selected stimulus configuration and its probability, and its numeric generation seed; signal arrays remain separate in memory. `simulate_trial` runs TVB and returns the selected state variables in the configured output dtype; `run_batches` distributes batches across a `ProcessPoolExecutor` controlled by `n_workers`, collects completions in the coordinator, and returns batches in batch order. The previous `joblib.Parallel` launcher remains commented out for reference.
- `notebooks/zerlaut/05_plot_simulations.ipynb` loads saved trials and their JSON configuration, and progressively plots the selected trial IDs in four columns using the plotting section from notebook 04.
- `notebooks/zerlaut/06_interactive_plot_simulations.ipynb` uses bqplot, ipywidgets, and ipyevents to load or remove up to 16 trials, decimate signals by 8, enlarge previews on hover, and compare parameters with JSON defaults using relative sampling density for color.
- `scripts/` is the destination for new executable Python scripts. It currently has no files.
- `src/aux/` contains reusable helpers imported directly from the checkout. It is not an installable distribution. The `aux.tvb` namespace keeps project helpers separate from the installed `tvb` library.
- `src/aux/parameters.py` contains parameter reshaping and sampling configuration helpers copied from notebook 02.
- `src/aux/tvb/model.py` provides model builders and `INTEGER_PARAMETERS_BY_MODEL`, used by notebook 04 to select integer parameter types by model name. `src/aux/tvb/integrator.py` provides `build_noise_config`, which selects additive noise on the model's `ou_drift` state for stochastic integrators and returns `None` for deterministic integrators. Notebook 04 derives both settings outside its configuration dictionary.
- `src/aux/tvb/stimulus.py` builds pulses, steps, smooth transitions, random variants, and additive noise with fixed or random standard deviation. Contributions are summed, including lists of the same type, using one generator seeded by `build_stimulus`. `ResultMetadata.stimulus_seed` is saved in NPZ metadata and used by `plot_results` by default; an explicit `stimulus_seed` overrides it. Files without this field load with `None`.
- `src/aux/sampling.py` contains Sobol, distribution, and sample-weight helpers copied from notebook 02. Notebook 02 keeps using its local definitions.
- `results/` contains generated outputs; its contents are ignored by Git.

The modular notebooks read the root dotenv files, add the configured import
directory to `sys.path`, and import `aux.environment` and `aux.tvb.*`. They keep
simulation parameters and execution steps in their cells. The extracted helper
functions do not depend on notebook-defined global values.

Parameter configuration and sampling fields use lowercase keys (`min`, `max`,
`default`, `std`, `method`, `lambda`). TVB parameter and state names keep their
original spelling, including `g_L`, `P_e`, and `E`.

## Maintenance rules

1. Read this file before modifying the repository structure or project files.
2. Do not write project code inside `0.sample_code/`.
3. Do not access `.prompts/`.
4. Update this file in the same change that alters a documented path or responsibility.
5. Keep the tree focused on maintained project files, not caches or temporary artifacts.
