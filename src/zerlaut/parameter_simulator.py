"""TVB simulator that updates model parameters before each integration step."""

import numpy as np
from tvb.basic.neotraits.api import List, NArray
from tvb.simulator.simulator import Simulator


class InputParameterSimulator(Simulator):
    """Apply time varying parameter values supplied per region."""

    input_parameters = List(
        of=tuple,
        default=(),
        label="Time varying model parameters",
        doc=(
            "Each entry is (parameter_name, source). Source is an array of "
            "shape (steps, regions) or (steps, 1), a function f(time_ms) "
            "returning one scalar for all regions, or one scalar function "
            "per region. For a constant value, set the model parameter directly."
        ),
    )

    def configure(self, full_configure=True):
        # Let TVB configure the model, connectivity, and optional surface.
        super().configure(full_configure=full_configure)

        # Validate the input parameter sources.
        n_regions = self.connectivity.number_of_regions
        names = set()
        self._parameter_updates = []
        for name, source in self.input_parameters:
            # Reject duplicate parameter names.
            if name in names:
                raise ValueError(f"Duplicate parameter: {name}")
            names.add(name)

            descriptor = getattr(type(self.model), name, None)
            if not isinstance(descriptor, NArray):
                raise ValueError(f"Unknown numeric parameter: {name}")
            current = np.asarray(getattr(self.model, name))
            if current.size not in (1, self.number_of_nodes) or not np.issubdtype(
                current.dtype, np.floating
            ):
                raise ValueError(f"{name} must contain real values per region")

            if isinstance(source, np.ndarray):
                if source.ndim != 2 or source.shape[1] not in (1, n_regions):
                    raise ValueError(
                        f"{name} needs an array of shape (steps, regions) or (steps, 1)"
                    )

                def values_at(step, time_ms, data=source, parameter_name=name):
                    if step >= len(data):
                        raise ValueError(f"Missing {parameter_name} values at step {step + 1}")
                    return data[step]

            elif callable(source):
                def values_at(step, time_ms, function=source, parameter_name=name):
                    value = np.asarray(function(time_ms), dtype=float)
                    if value.ndim != 0:
                        raise ValueError(f"{parameter_name} function must return one scalar")
                    return value

            elif (
                isinstance(source, (list, tuple))
                and len(source) == n_regions
                and all(map(callable, source))
            ):
                def values_at(step, time_ms, functions=tuple(source)):
                    return [function(time_ms) for function in functions]

            else:
                raise ValueError(
                    f"{name} needs an array, a function, or one function per region"
                )

            self._parameter_updates.append((name, values_at))
        return self

    def _loop_update_stimulus(self, step, stimulus):
        super()._loop_update_stimulus(step, stimulus)

        index = step - 1  # Step 1 starts at t=0.
        time_ms = index * self.integrator.dt

        n_regions = self.connectivity.number_of_regions
        for name, values_at in self._parameter_updates:
            values = np.asarray(values_at(index, time_ms), dtype=float)
            if values.shape not in ((), (1,), (n_regions,)):
                raise ValueError(f"{name} must provide one scalar or one value per region")
            values = np.broadcast_to(values, (n_regions,))
            if self.surface is not None:
                values = values[self.surface.region_mapping]
            setattr(self.model, name, values[:, np.newaxis])
