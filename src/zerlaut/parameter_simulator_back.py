"""Simulador TVB que actualiza parámetros del modelo antes de cada paso."""

import numpy as np
from tvb.basic.neotraits.api import List, NArray
from tvb.simulator.simulator import Simulator


class ParameterSimulator(Simulator):
    """Aplica pares (nombre, array o función) a parámetros por región."""

    input_parameters = List(
        of=tuple,
        default=(),
        label="Parámetros de entrada variables en el tiempo",
    )

    @staticmethod
    def _region_functions(source):
        return (
            isinstance(source, (list, tuple, np.ndarray))
            and np.ndim(source) == 1
            and all(callable(function) for function in source)
        )

    def configure(self, full_configure=True):
        if self.surface is not None:
            raise ValueError("ParameterSimultor does not support surface simulations")

        super().configure(full_configure=full_configure)

        names = set()
        for name, source in self.input_parameters:
            if name in names:
                raise ValueError(f"Parámetro repetido: {name}")
            names.add(name)

            descriptor = getattr(type(self.model), name, None)
            if not isinstance(descriptor, NArray):
                raise ValueError(f"Parámetro numérico desconocido: {name}")
            current = np.asarray(getattr(self.model, name))
            if current.size not in (1, self.number_of_nodes) or not np.issubdtype(
                current.dtype, np.floating
            ):
                raise ValueError(f"{name} debe ser un valor real por región")

            if self._region_functions(source):
                if len(source) != self.number_of_nodes:
                    raise ValueError(f"{name} necesita una función por región")
            elif not callable(source):
                if not isinstance(source, np.ndarray) or (
                    source.ndim != 2 or source.shape[1] != self.number_of_nodes
                ):
                    raise ValueError(
                        f"{name} necesita un array de forma (pasos, regiones)"
                    )
        return self

    def _loop_update_stimulus(self, step, stimulus):
        super()._loop_update_stimulus(step, stimulus)
        index = step - 1  # El paso 1 comienza en t=0.
        time_ms = index * self.integrator.dt

        for name, source in self.input_parameters:
            if callable(source):
                value = source(time_ms)
            elif self._region_functions(source):
                value = [function(time_ms) for function in source]
            else:
                if index >= len(source):
                    raise ValueError(f"Faltan valores para {name} en el paso {step}")
                value = source[index]

            values = np.asarray(value, dtype=float)
            if values.ndim == 0:
                values = values.reshape(1)
            if values.shape != (self.number_of_nodes,):
                raise ValueError(f"{name} debe dar un valor por región")
            setattr(self.model, name, values[:, np.newaxis])
