import numpy as np
from scipy.stats import qmc
from scipy.stats import beta, truncnorm



SEED = 42


def create_sobol(n_variables, seed=SEED):
    return qmc.Sobol(
        d=n_variables, scramble=True, seed=seed
    )


def _uniform_sample(s, minimum, maximum):
    scale= maximum - minimum
    return minimum + s * scale, 1/scale


def _truncnorm_sample(s, minimum, maximum, peak, std):
    a = (minimum - peak) / std
    b = (maximum - peak) / std
    dist = truncnorm(a, b, loc=peak, scale=std)
    return (value := dist.ppf(s)), dist.pdf(value)


def _beta_sample(s, minimum, maximum, peak, lam):
    relative_peak = (peak - minimum) / (maximum - minimum)
    a = 1 + relative_peak * lam
    b = 1 + (1 - relative_peak) * lam
    dist = beta(a, b, loc=minimum, scale=maximum - minimum)
    return (value := dist.ppf(s)), dist.pdf(value)

def _sample_from_pdf(s, param):
    minimum = param["MIN"]
    maximum = param["MAX"]

    match param.get("METHOD", "uniform"):
        case "truncnorm":
            return _truncnorm_sample(
                s, minimum, maximum, param["DEFAULT"], param["STD"]
            )
        case "beta":
            return _beta_sample(
                s, minimum, maximum, param["DEFAULT"], param["LAMBDA"]
            )
        case _:
            return _uniform_sample(s, minimum, maximum)


def sample_params(params, n_samples, fordware=0, seed=42):
    sampler = qmc.Sobol(d=len(params), scramble=True, seed=seed)
    if fordware > 0:
        sampler.fast_forward(fordware)

    for s in sampler.random(n_samples):
        values, densities = {}, {}
        for i, (name, config) in enumerate(params.items()):
            value, density = _sample_from_pdf(s[i], config)
            values[name] = value
            densities[name] = density

        yield values, densities

        # # Mas elegante, pero menos eficiente
        # values, densities = zip(*map(_sample_from_pdf, s, params.values()))
        # yield dict(zip(params, values)), dict(zip(params, densities))


def sample_weight(pdfs, alpha=0.5):
    return (1 - alpha) + alpha / np.prod(list(pdfs.values()))
