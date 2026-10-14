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
            group = result.setdefault(base, {})
            for k, v in config.items():
                group.setdefault(k, []).append(v)
    return result


def add_truncnorm_config(params, std_factor=0.2):
    result =deepcopy(params)

    for name in result.keys():
        result[name]["std"]= (result[name]["max"] - result[name]["min"]) * std_factor
        result[name]["method"] = "truncnorm"

    return result

def add_beta_config(params, lambda_):
    result =deepcopy(params)

    for name in result.keys():
        result[name]["lambda"] = lambda_
        result[name]["method"] = "beta"

    return result
