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
│   ├── simulation.json        # Retained configuration from earlier examples
│   └── parameter_ranges.json  # Reference parameter ranges
├── notebooks/
│   └── zerlaut/
│       ├── simulation_step_by_step.ipynb
│       └── simulation_step_by_step_funcs.ipynb
├── scripts/                   # Future executable scripts: <topic>/<name>.py
├── src/                       # Directly imported helpers; no build metadata
│   ├── __init__.py
│   ├── environment.py          # Resolve working and results directories
│   └── tvb/
│       ├── __init__.py
│       ├── stimulus.py         # Pulse and pulse-train arrays
│       ├── model.py            # Model builder
│       ├── integrator.py       # Integrator and noise builder
│       ├── simulator.py        # Dynamic parameters and single-region simulator
│       ├── results.py          # Result metadata and NPZ persistence
│       └── plotting.py         # Result plots
└── results/                   # Generated NPZ files; ignored by Git
```

## Responsibilities and relationships

- `AGENTS.MD` contains mandatory repository instructions for agents.
- `README.md` explains how to prepare the environment and run the notebooks.
- `VBT_4-3.MD` indexes the external reference code in `0.sample_code/sinovia`.
- `0.sample_code/` is external reference material and must not be modified.
- `.prompts/` is reserved for the user and must not be accessed by agents.
- `.env_default` contains tracked path defaults, including `TVB_IMPORT_DIR` for the directory containing `src/`. The ignored `.env` may override them locally. Neither file contains simulation or model values.
- `conda/environment.yml` defines the Python environment, including `python-dotenv`, `json5`, and TVB.
- `config/` retains configuration files from the earlier script layout; neither current notebook reads them.
- `notebooks/zerlaut/simulation_step_by_step.ipynb` is the original, self-contained teaching notebook.
- `notebooks/zerlaut/simulation_step_by_step_funcs.ipynb` preserves the same simulation workflow and values while importing helper definitions from `src/`.
- `scripts/` is the destination for new executable Python scripts. It currently has no files.
- `src/` contains reusable helpers imported directly from the checkout. It is not an installable distribution. The `src.tvb` namespace keeps project helpers separate from the installed `tvb` library.
- `results/` contains generated outputs; its contents are ignored by Git.

The modular notebook reads the root dotenv files, adds `TVB_IMPORT_DIR` to
`sys.path` (or the dotenv directory if unset), and imports `src.environment`
and `src.tvb.*`. The notebook keeps
simulation parameters and execution steps in its cells. The extracted helper
functions do not depend on notebook-defined global values.

## Maintenance rules

1. Read this file before modifying the repository structure or project files.
2. Do not write project code inside `0.sample_code/`.
3. Do not access `.prompts/`.
4. Update this file in the same change that alters a documented path or responsibility.
5. Keep the tree focused on maintained project files, not caches or temporary artifacts.
