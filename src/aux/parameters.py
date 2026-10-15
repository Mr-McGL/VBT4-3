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

    return result

def add_beta_config(params, lambda_, names=None):
    result = deepcopy(params)

    selected_names = result if names is None else names

    for name in selected_names:
        config = result[name]
        config["lambda"] = lambda_
        config["method"] = "beta"

    return result

def add_beta_config_safe(params, lambda_, names=None):
    flat = flatten_params(params)
    return restore_flat_params(add_beta_config(flat, lambda_=lambda_, names=names))


def add_truncnorm_config_safe(params, std_factor=0.2, names=None):
    flat = flatten_params(params)
    return restore_flat_params(add_truncnorm_config(flat, std_factor=std_factor, names=names))


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