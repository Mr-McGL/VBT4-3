import numpy as np
from tvb.basic.neotraits.api import List, NArray
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.coupling import Linear
from tvb.simulator.monitors import Raw
from tvb.simulator.simulator import Simulator


class DynamicParameterSimulator(Simulator):
    """Apply time varying parameter values to regions or nodes."""

    dynamic_parameters = List(
        of=tuple,
        default=(),
        label="Time varying model parameters",
        doc=(
            "Each entry is (parameter_name, source). Source is an array of "
            "shape (steps, regions), (steps, nodes), or (steps, 1), or a "
            "sequence of scalar functions for each region, each node, or all "
            "nodes. For a constant value, set the model parameter directly."
        ),
    )

    def configure(self, full_configure=True):
        # Let TVB configure the model, connectivity, and optional surface.
        super().configure(full_configure=full_configure)

        # Validate each source and remember how to read it during the run.
        n_regions, n_nodes = self.connectivity.number_of_regions, self.number_of_nodes
        self._parameter_sources, names = [], set()
    
        for name, source in self.dynamic_parameters:
            # Reject duplicate parameter names.
            if name in names:
                raise ValueError(f"Duplicate parameter: {name}")
            names.add(name)

            # Validate that the parameter exists and is a numeric array.
            descriptor = getattr(type(self.model), name, None)
            if not isinstance(descriptor, NArray):
                raise ValueError(f"Unknown numeric parameter: {name}")

            # ToDo: Validate the type of the array. 
            # ToDo:Por ahora solo funciona para floats

            # Validate the source type and shape.
            source_type = "invalid"
            if isinstance(source, np.ndarray):
                if source.ndim != 2:
                    source_type = "invalid"
                elif self.surface is not None and source.shape[1] == n_nodes: # It must be the first
                     source_type = "node_array"
                elif source.shape[1] == n_regions:
                    source_type = "region_array"
                elif source.shape[1] == 1:
                    source_type = "scalar_array" # It must be the last

            elif (
                isinstance(source, (list, tuple))
                and all(map(callable, source))
            ):
                if self.surface is not None and len(source) == n_nodes: # It must be the first
                    source_type = "node_functions"
                elif len(source) == n_regions:
                    source_type = "region_functions"
                elif len(source) == 1: # It must be the last
                    source_type = "scalar_function"
                

            if source_type == "invalid":
                raise ValueError(
                    f"{name} needs an array or one function per region or node"
                )

            self._parameter_sources.append((name, source, source_type))
        return self

    def _loop_update_stimulus(self, step, stimulus):
        super()._loop_update_stimulus(step, stimulus)

        index = step - 1  # Step 1 starts at t=0.
        time_ms = index * self.integrator.dt

        n_regions = self.connectivity.number_of_regions
        for name, source, source_type in self._parameter_sources:
            match source_type:
                case "region_array" | "node_array": 
                    values = source[index]
                case "scalar_array": 
                    values = np.full(self.number_of_nodes, source[index, 0])
                case "scalar_function": 
                    values = np.full(self.number_of_nodes, source[0](time_ms))
                case "region_functions" | "node_functions": 
                    values = [function(time_ms) for function in source]

            # ToDo: Por ahora esta restringido floats. 
            values = np.asarray(values, dtype=float)
            
            if self.surface is not None and source_type.startswith("region_"):
                values = values[self.surface.region_mapping]
   
            setattr(self.model, name, values[:, np.newaxis])


def build_single_region_simulator(model, stimulus, integrator):
    return DynamicParameterSimulator(
        model=model,
        dynamic_parameters=stimulus,
        # stimulus= Value for variables in model.stvars 
        # state_variables todas, cvar acoplables, stvar estimulables.
        
        connectivity=Connectivity(
            weights=np.zeros((1, 1)),
            tract_lengths=np.zeros((1, 1)),
            speed=np.array([3.0]), # mm/ms; una velocidad común para las conexiones.
            # idelays (N, N) (steps)
            #delays` (N, N)
            centres=np.zeros((1, 3)),
            region_labels=np.array(["región"]),
        ),
        coupling=Linear(a=np.array([0.0])),
        # conduction_speed, redundante no usar

        integrator=integrator,
        monitors=(Raw(),),
        # initial_conditions=np.zeros((1, model.n_state_variables, 1, model.number_of_modes)), # history, state, region, node
        initial_conditions=np.zeros((1, len(model.state_variables), 1, 1))
    ).configure()
