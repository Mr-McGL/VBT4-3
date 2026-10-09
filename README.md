# Single-region TVB simulation

This repository contains a step-by-step notebook for a single-region simulation
with TVB's Zerlaut adaptation models. The notebook keeps its model parameters,
stimulus values, simulation steps, and result handling visible in its cells.

## Environment

Create and activate the environment from the repository root:

```bash
micromamba create -f conda/environment.yml
micromamba activate tvb
```

The environment includes `python-dotenv`, `json5`, and `tvb-library`. Launch
Jupyter from the repository root:

```bash
jupyter lab notebooks/zerlaut/simulation_step_by_step.ipynb
```

The original notebook is self-contained. To run the copy that imports auxiliary
code from `src/`, open:

```bash
jupyter lab notebooks/zerlaut/simulation_step_by_step_funcs.ipynb
```

The modular notebook first reads `.env_default` with `python-dotenv`, then lets
the ignored local `.env` override it. `TVB_IMPORT_DIR` points to the directory
containing `src/`; relative values are resolved from the location of
`.env_default`. If the variable is absent or empty, the notebook uses that
location directly. Run its cells in order.
`TVB_WORK_DIR` is resolved relative to the repository root, and
`TVB_RESULTS_DIR` is resolved relative to `TVB_WORK_DIR`. Either may be an
absolute path. Simulation and model values remain in the notebook.

## Layout

- `notebooks/zerlaut/simulation_step_by_step.ipynb`: original teaching notebook.
- `notebooks/zerlaut/simulation_step_by_step_funcs.ipynb`: the same workflow with auxiliary definitions imported from `src/`.
- `src/environment.py`: directory resolution.
- `src/tvb/stimulus.py`: pulse and pulse-train construction.
- `src/tvb/model.py`: TVB model construction.
- `src/tvb/integrator.py`: TVB integrator and noise construction.
- `src/tvb/simulator.py`: time-varying parameter simulator and single-region setup.
- `src/tvb/results.py`: result metadata and NPZ save/load functions.
- `src/tvb/plotting.py`: result plots.
- `scripts/<topic>/<script_name>.py`: location for future executable scripts; there are currently no scripts.
- `config/`: retained JSON configurations and parameter ranges from earlier examples.
- `results/`: generated outputs, ignored by Git.

The code under `src/` is imported directly from the checkout and is not an
installable distribution. Its `src.tvb` import path distinguishes these helpers
from the installed `tvb` library.
