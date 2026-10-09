import matplotlib.pyplot as plt
import numpy as np
from src.tvb.stimulus import build_stimulus


def plot_results(times, states, metadata, show_stimulus=True, ax=None, plot_states=None):
    times = np.asarray(times)
    if plot_states is None:
        plotted_states = states
    else:
        if isinstance(plot_states, str):
            plot_states = [plot_states]
        plotted_states = {name: states[name] for name in plot_states}

    state_units = metadata.model.state_units or {}
    stimulus_units = metadata.model.stimulus_units or {}
    groups = []

    if show_stimulus:
        stimulus_times, stimulus_data = build_stimulus(
            metadata.stimulus,
            metadata.simulation.duration_ms,
            metadata.simulation.dt_ms,
        )
        units = dict.fromkeys(stimulus_units.get(name, "model units")
                              for name, _ in stimulus_data)
        for unit in units:
            signals = [(name, values) for name, values in stimulus_data
                       if stimulus_units.get(name, "model units") == unit]
            groups.append(("Stimuli", unit, signals))

    units = dict.fromkeys(state_units.get(name, "model units") for name in plotted_states)
    for unit in units:
        names = [name for name in plotted_states
                 if state_units.get(name, "model units") == unit]
        groups.append(("State variables", unit, names))

    if ax is None:
        fig, axes = plt.subplots(
            len(groups), 1, figsize=(11, 3 * len(groups)),
            sharex=True, squeeze=False, constrained_layout=True,
        )
        axes = axes[:, 0]
    else:
        fig = ax.figure
        subplotspec = ax.get_subplotspec()
        position = ax.get_position()
        ax.remove()
        if subplotspec is None:
            grid = fig.add_gridspec(
                len(groups), 1, left=position.x0, right=position.x1,
                bottom=position.y0, top=position.y1,
            )
        else:
            grid = subplotspec.subgridspec(len(groups), 1)
        axes = []
        for i in range(len(groups)):
            axes.append(fig.add_subplot(grid[i], sharex=axes[0] if axes else None))
        axes = np.asarray(axes)

    for axis, (kind, unit, data) in zip(axes, groups):
        if kind == "Stimuli":
            edges = np.r_[stimulus_times, times[-1]]
            for name, values in data:
                axis.stairs(np.asarray(values).ravel(), edges, label=name)
        else:
            for name in data:
                axis.plot(times, plotted_states[name], label=name)
        axis.set_ylabel(f"{kind} ({unit})")
        axis.grid(alpha=0.25)
        axis.legend()
    axes[-1].set_xlabel("Time (ms)")
    return fig, axes
