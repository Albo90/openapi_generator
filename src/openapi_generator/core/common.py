import json
import pprint
from pathlib import Path
from typing import Dict, Any


def read_json_file(path: Path) -> Dict[str, Any]:
    with open(path) as f:
        data = json.load(f)
    return data


def truncate_string(item):
    if isinstance(item, list):
        new_item = list()
        for i in range(0, len(item)):
            new_item.append(truncate_string(item[i]))
    elif isinstance(item, dict):
        new_item = dict()
        for key, value in item.items():
            new_item[key] = truncate_string(value)
    elif isinstance(item, str):
        if len(item) > 40:
            new_item = f'{item[:40]}...'
        else:
            new_item = item
    else:
        new_item = item
    return new_item


def clean_print(item):
    pprint.pprint(truncate_string(item), indent=2)
