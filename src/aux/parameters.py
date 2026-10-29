from copy import deepcopy


def flatten_params(params):
    flat = {}
    for name, config in params.items():
        first = next(iter(config.values()))
        if isinstance(first, list):
            for i in range(len(first)):
                flat[f"{name}*{i:02}"] = {k: v[i] for k, v in config.items()}
        else:
            flat[name] = config
    return flat


def restore_flat_params(flat_params):
    result = {}
    for name, config in sorted(flat_params.items()):
        base, sep, _ = name.partition("*")
        if not sep:
            result[name] = config
        else:
            if isinstance(config, dict):
                group = result.setdefault(base, {})
                for k, v in config.items():
                    group.setdefault(k, []).append(v)
            else:
                result.setdefault(base, []).append(config)


    return result


def add_truncnorm_config(params, std_factor=0.2, names=None):
    result = deepcopy(params)

    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]
        config["std"] = (config["max"] - config["min"]) * std_factor
        config["method"] = "truncnorm"
        config["a"] = (config["min"] - config["default"]) / config["std"] 
        config["b"] = (config["max"] - config["default"]) / config["std"] 
        config["loc"] = config["default"]
        config["scale"] = config["std"]
        config["config_source"] = "simple"

    return result

def add_beta_config(params, lambda_, names=None):
    result = deepcopy(params)

    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]
        config["lambda"] = lambda_
        config["method"] = "beta"
        scale = config["max"] - config["min"]
        relative_peak = (config["default"] - config["min"]) / scale
        config["a"] = 1 + relative_peak * lambda_
        config["b"] = 1 + (1 - relative_peak) * lambda_
        config["loc"] = config["min"]
        config["scale"] = scale
        config["config_source"] = "simple"

    return result

def add_truncnorm_config_pdf(params, a, b, loc=0.0, scale=1.0, names=None):
    result = deepcopy(params)
    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]
        config.update(a=a, b=b, loc=loc, scale=scale, method="truncnorm",
                      config_source="raw_pdf")

    return result


def add_beta_config_pdf(params, a, b, loc=0.0, scale=1.0, names=None):
    """Use SciPy PDF parameters a, b, loc, scale; preserve min/max as clamps."""
    result = deepcopy(params)
    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]
        config.update(a=a, b=b, loc=loc, scale=scale, method="beta",
                      config_source="raw_pdf")

    return result


# Configure scalar and list-valued parameters without modifying the input.
def add_beta_config_safe(params, lambda_, names=None):
    flat = flatten_params(params)
    return restore_flat_params(add_beta_config(flat, lambda_=lambda_, names=names))


def add_truncnorm_config_safe(params, std_factor=0.2, names=None):
    flat = flatten_params(params)
    return restore_flat_params(add_truncnorm_config(flat, std_factor=std_factor, names=names))

def add_beta_config_pdf_safe(params, a, b, loc=0.0, scale=1.0, names=None):
    flat = flatten_params(params)
    return restore_flat_params(add_beta_config_pdf(flat, a, b, loc=loc, scale=scale, names=names))


def add_truncnorm_config_pdf_safe(params, a, b, loc=0.0, scale=1.0, names=None):
    flat = flatten_params(params)
    return restore_flat_params(add_truncnorm_config_pdf(flat, a, b, loc=loc, scale=scale, names=names))


def affine(parameter, factor=1.0, offset=0.0):
    return {"parameter": parameter, "factor": factor, "offset": offset}


def _add_dependent_config(params, method, afin_default, afin_min, afin_max, names, **settings):
    result = deepcopy(params)
    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]
        config.update(settings)
        config["method"] = method
        config["config_source"] = "affine"
        for key, reference in (("afin_default", afin_default), ("afin_min", afin_min), ("afin_max", afin_max)):
            if reference is not None:
                config[key] = reference

    return result

def add_beta_config_dependent(params, lambda_, afin_default=None, afin_min=None, afin_max=None, names=None):
    return _add_dependent_config(params, "beta", afin_default, afin_min, afin_max, names,
                                 **{"lambda": lambda_}) #Asi se evita el problema usar una palabra reservada.


def add_truncnorm_config_dependent(params, std_factor=0.2, afin_default=None, afin_min=None, afin_max=None, names=None):
    return _add_dependent_config(params, "truncnorm", afin_default, afin_min, afin_max, names,
                                 std_factor=std_factor)


def add_uniform_config_dependent(params, afin_default=None, afin_min=None, afin_max=None, names=None):
    return _add_dependent_config(params, "uniform", afin_default, afin_min, afin_max, names)


def _adjust_value(value, margin, sign):
    if isinstance(value, list):
        return [v + sign * abs(v) * margin for v in value]
    return value + sign * abs(value) * margin


def bounds_from_default(params, names=None, margin=0.10):
    result = deepcopy(params)
    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]
        default = config["default"]

        config["min"] = _adjust_value(default, margin, -1)
        config["max"] = _adjust_value(default, margin, 1)

    return result


def expand_bounds(params, names=None, margin=0.10):
    if margin < 0:
        raise ValueError("Variation must be non-negative.")

    result = deepcopy(params)
    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]

        config["min"] = _adjust_value(config["min"], margin, -1)
        config["max"] = _adjust_value(config["max"], margin, 1)

    return result


def filter_nested_dict(data: dict, keys: list[str]) -> dict:
    return {
        name: {key: value for key, value in params.items() if key in keys}
        for name, params in data.items()
    }