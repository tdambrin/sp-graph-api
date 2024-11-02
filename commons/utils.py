from pathlib import Path
from typing import Any, Dict, List, Union
from copy import deepcopy

import yaml
import numpy as np


def load_from_yml(
    path: Union[str, Path]
) -> Dict[str, Any]:
    with open(path, "r") as f:
        content = yaml.safe_load(f)
    return content


def values_to_str(values: Union[List[str], str], sep: str = ",") -> str:
    if isinstance(values, str):
        return values
    return sep.join([value.strip() for value in values])


def str_to_values(values: str, sep: str = ",") -> List[str]:
    return [value.strip() for value in values.split(sep)]


def dict_extend(*args):
    """
    same as {**d1, **d2} but add overlapping values instead of overriding
    """
    d = {}
    for entry in args:
        for key in entry:
            if d.get(key):
                d[key] += deepcopy(entry)[key]
            else:
                d[key] = deepcopy(entry)[key]
    return d


def scale_weights(
    relative_weights: List[int],
    target_sum: int,
    include_all: bool = True,
):
    """
    Scale list of weights for total sum. Puts at least one of initial weights.
    e.g. ([1, 2], 2) => [1, 1] because target sum smaller than weights and at least one each
    e.g. ([1, 2], 3) => [1, 2] because target sum == total weights
    e.g. ([1, 2], 5) => [2, 3] because target sum > total weights, at least one of each and tries to respect initial weights
    Args:
        relative_weights: weights of each index
        target_sum: sum(res) should be this
        include_all: bool whether every bin should have at least 1

    Returns:
        list of weights adjusted summing up to target_sum
    """  # noqa: E501
    if target_sum < len(relative_weights) and include_all:
        raise ValueError(
            "[Error: utils.scale_weights] "
            "Target sum smaller than number of bins, would result in bins deletion "
            f"target_sum={target_sum}, relative_weights: {relative_weights}"
        )
    N = len(relative_weights)
    res = [1] * N if include_all else [0] * N
    remaining = [w-1 for w in relative_weights] if include_all else relative_weights.copy()
    used = N if include_all else 0
    _next = np.argmax(remaining)
    while used < target_sum and remaining[_next] > 0:
        remaining[_next] -= 1
        res[_next] += 1
        used += 1
        _next = np.argmax(remaining)

    if used < target_sum:
        res = [
            sum(weights)
            for weights in zip(
                res,
                scale_weights(relative_weights, target_sum - used, include_all=False)
            )
        ]

    return res
