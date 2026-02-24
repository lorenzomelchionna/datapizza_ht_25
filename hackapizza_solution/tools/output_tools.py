"""Tools for mapping dish names to IDs and formatting final output."""

import json
from pathlib import Path

from datapizza.tools import tool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import DISH_MAPPING_JSON

_mapping_cache: dict[str, int] | None = None


def _load_mapping() -> dict[str, int]:
    global _mapping_cache
    if _mapping_cache is None:
        _mapping_cache = json.loads(DISH_MAPPING_JSON.read_text(encoding="utf-8"))
    return _mapping_cache


@tool
def map_dishes_to_ids(dish_names: str) -> str:
    """Convert a comma-separated list of dish names to their numeric IDs.
    Uses dish_mapping.json. Returns ONLY the IDs as a comma-separated string.
    Example input: "Cosmic Harmony,Sinfonia Cosmica"
    Example output: "IDS: 9,204"
    """
    mapping = _load_mapping()
    names = [n.strip() for n in dish_names.split(",") if n.strip()]
    found_ids = []
    warnings = []
    for name in names:
        if name in mapping:
            found_ids.append(mapping[name])
        else:
            matched = False
            for known_name, dish_id in mapping.items():
                if name.lower() == known_name.lower():
                    found_ids.append(dish_id)
                    matched = True
                    break
            if not matched:
                candidates = [
                    (k, v) for k, v in mapping.items()
                    if name.lower() in k.lower() or k.lower() in name.lower()
                ]
                if len(candidates) == 1:
                    found_ids.append(candidates[0][1])
                else:
                    warnings.append(name)

    found_ids = sorted(set(found_ids))
    ids_str = ",".join(str(i) for i in found_ids)
    result = f"IDS: {ids_str}"
    if warnings:
        result += f"\nNOT FOUND: {', '.join(warnings)}"
    return result
