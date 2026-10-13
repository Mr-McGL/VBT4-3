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
│           ├── stimulus.py     # Pulse and pulse-train arrays
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
- `conda/environment.yml` defines the Python environment, including `python-dotenv`, `json5`, and TVB.
- `config/zerlaut/params_raw.json` stores Zerlaut parameter data.
- `notebooks/zerlaut/01a_simulation_one_region.ipynb` is the original single-region teaching example.
- `notebooks/zerlaut/01b_simulation_one_region.ipynb` uses the helpers in `src/aux/` for single-region simulations.
- `notebooks/zerlaut/01c_simulation_one_region.ipynb` compares external stimulation signals.
- `notebooks/zerlaut/01d_simulation_two_regions.ipynb` explores signal tracking and directed coupling.
- `notebooks/zerlaut/01e_simulation_one_region.ipynb` compares `weight_noise` and `tau_OU` under a constant baseline input.
- `notebooks/zerlaut/03_parameter_exploration.ipynb` groups Zerlaut defaults, counts parameters, explores ranges, and runs a noise-parameter simulation grid.
- `notebooks/zerlaut/02_sampling_test.ipynb` and `99a_simulation_configuration.ipynb` contain additional Zerlaut experiments.
- `scripts/` is the destination for new executable Python scripts. It currently has no files.
- `src/aux/` contains reusable helpers imported directly from the checkout. It is not an installable distribution. The `aux.tvb` namespace keeps project helpers separate from the installed `tvb` library.
- `src/aux/parameters.py` contains parameter reshaping and sampling configuration helpers copied from notebook 02.
- `src/aux/sampling.py` contains Sobol, distribution, and sample-weight helpers copied from notebook 02. Notebook 02 keeps using its local definitions.
- `results/` contains generated outputs; its contents are ignored by Git.

The modular notebooks read the root dotenv files, add the configured import
directory to `sys.path`, and import `aux.environment` and `aux.tvb.*`. They keep
simulation parameters and execution steps in their cells. The extracted helper
functions do not depend on notebook-defined global values.

## Maintenance rules

1. Read this file before modifying the repository structure or project files.
2. Do not write project code inside `0.sample_code/`.
3. Do not access `.prompts/`.
4. Update this file in the same change that alters a documented path or responsibility.
5. Keep the tree focused on maintained project files, not caches or temporary artifacts.
