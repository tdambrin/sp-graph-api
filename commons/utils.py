from pathlib import Path
from typing import Any, Dict, List, Union
from copy import deepcopy

import yaml


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
    d = {}
    for entry in args:
        for key in entry:
            if d.get(key):
                d[key] += deepcopy(entry)[key]
            else:
                d[key] = deepcopy(entry)[key]
    return d
