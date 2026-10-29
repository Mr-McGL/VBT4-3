import numpy as np
from scipy.stats import qmc
from scipy.stats import beta, truncnorm


SEED = 42


def create_sobol(n_variables, seed=SEED):
    return qmc.Sobol(
        d=n_variables, scramble=True, seed=seed
    )


#TODO: Crear una clase que ya tenga creadas las distribuciones por
#parametro.

def _uniform_sample(s, minimum, maximum):
    scale= maximum - minimum
    return minimum + s * scale, 1/scale


def _truncnorm_sample(s, a, b, loc, scale):
    # TODO
    # Tighten even hardcoded a/b to min/max, preserving any narrower original bounds.
    # a = max(a, (minimum - loc) / scale)
    # b = min(b, (maximum - loc) / scale)
    dist = truncnorm(a, b, loc=loc, scale=scale)
    value = dist.ppf(s)
    return value, dist.pdf(value)


def _beta_sample(s, a, b, loc, scale):
    # Truncate through the CDF and normalize the PDF, keeping a, b, loc and scale.
    # dist = beta(a, b, loc=loc, scale=scale)
    # cdf_min = dist.cdf(minimum)
    # cdf_max = dist.cdf(maximum)
    # mass = cdf_max - cdf_min
    # if mass <= 0:
    #     loc = minimum
    #     scale = maximum - minimum
    dist = beta(a, b, loc=loc, scale=scale)
    value = dist.ppf(s)
    return value, dist.pdf(value)

def _sample_from_pdf(s, param):
    minimum, maximum = param["min"], param["max"]
    if minimum == maximum:
        return minimum, 1.0
        
    match param.get("method", "uniform"):
        case "truncnorm":
            return _truncnorm_sample(
                s, param["a"], param["b"], param["loc"], param["scale"]
            )
        case "beta":
            return _beta_sample(
                s, param["a"], param["b"], param["loc"], param["scale"]
            )
        case _:
            return _uniform_sample(s, minimum, maximum)

def _affine_value(reference, values):
    if isinstance(reference, dict):
        return reference["factor"] * values[reference["parameter"]] + reference["offset"]
    return reference


def _sample_dependent(s, config, values):
    # Resolve affine fields for this sample using local values only.
    minimum = _affine_value(config.get("afin_min", config["min"]), values)
    maximum = _affine_value(config.get("afin_max", config["max"]), values)
    peak = _affine_value(config.get("afin_default", config["default"]), values)
    minimum, maximum = max(minimum, config["min"]), min(maximum, config["max"])

    # TODO: No hay control de errores si hay una mala configuración. En el caso anterior,
    # tampoco, pero aquí puede ser más fastidioso de entcontar.
    if minimum > config["max"]: minimum = config["max"]
    if minimum >= maximum: return minimum, 1.0
    if peak < minimum: peak = minimum
    elif peak > maximum: peak = maximum


    match config["method"]:
        case "beta":
            scale = maximum - minimum
            relative_peak = (peak - minimum) / scale
            a = 1 + relative_peak * config["lambda"]
            b = 1 + (1 - relative_peak) * config["lambda"]
            return _beta_sample(s, a, b, minimum, scale)
        case "truncnorm":
            std = (maximum - minimum) * config["std_factor"]
            a, b = (minimum - peak) / std, (maximum - peak) / std
            return _truncnorm_sample(s, a, b, peak, std)
        case _:
            return _uniform_sample(s, minimum, maximum)


def sample_params(params, n_samples, fordware=0, seed=42):
    sampler = qmc.Sobol(d=len(params), scramble=True, seed=seed)
    if fordware > 0:
        sampler.fast_forward(fordware)

    normal_params, dependent_params = [], []
    for i, (name, config) in enumerate(params.items()):
        selected = dependent_params if config.get("config_source") == "affine" else normal_params
        selected.append((i, name, config))

    for s in sampler.random(n_samples):
        values, densities = {}, {}
        for i, name, config in normal_params:
            value, density = _sample_from_pdf(s[i], config)
            values[name] = value
            densities[name] = density

        for i, name, config in dependent_params:
            value, density = _sample_dependent(s[i], config, values)
            values[name] = value
            densities[name] = density

        yield values, densities

        # # Mas elegante, pero menos eficiente
        # values, densities = zip(*map(_sample_from_pdf, s, params.values()))
        # yield dict(zip(params, values)), dict(zip(params, densities))


def sample_weight(pdfs, alpha=0.5):
    return (1 - alpha) + alpha / np.prod(list(pdfs.values()))
