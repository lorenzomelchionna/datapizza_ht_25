"""Tools for mapping dish names to IDs and formatting final output."""

import json
from pathlib import Path

from datapizza.tools import tool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import DISH_MAPPING_JSON, MENUS_JSON

_mapping_cache: dict[str, int] | None = None
_menus_cache: list[dict] | None = None


def _load_mapping() -> dict[str, int]:
    global _mapping_cache
    if _mapping_cache is None:
        _mapping_cache = json.loads(DISH_MAPPING_JSON.read_text(encoding="utf-8"))
    return _mapping_cache


def _load_menus() -> list[dict]:
    global _menus_cache
    if _menus_cache is None and MENUS_JSON.exists():
        _menus_cache = json.loads(MENUS_JSON.read_text(encoding="utf-8"))
    return _menus_cache or []


def _find_dishes_by_ingredient_or_technique(search_str: str) -> list[str]:
    """Fallback: find dish names where search_str matches an ingredient or technique.
    Handles cases like 'Ravioli al Vaporeon in Brodo' matching ingredient 'Ravioli al Vaporeon'."""
    menus = _load_menus()
    mapping = _load_mapping()
    found_names = []
    search_lower = search_str.lower()
    for menu in menus:
        for dish in menu.get("dishes", []):
            name = dish.get("name", "")
            if name not in mapping:
                continue
            matched = False
            for ing in dish.get("ingredients", []):
                ing_lower = str(ing).lower()
                if search_lower in ing_lower or ing_lower in search_lower:
                    found_names.append(name)
                    matched = True
                    break
            if not matched:
                for tech in dish.get("techniques", []):
                    tech_lower = str(tech).lower()
                    if search_lower in tech_lower or tech_lower in search_lower:
                        found_names.append(name)
                        break
    return list(dict.fromkeys(found_names))


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
                    matched = True
            if not matched:
                # Fallback: name might be an ingredient/technique - find dishes containing it
                dish_names_from_menu = _find_dishes_by_ingredient_or_technique(name)
                if dish_names_from_menu:
                    for dn in dish_names_from_menu:
                        if dn in mapping:
                            found_ids.append(mapping[dn])
                    matched = True
                if not matched:
                    warnings.append(name)

    found_ids = sorted(set(found_ids))
    ids_str = ",".join(str(i) for i in found_ids)
    result = f"IDS: {ids_str}"
    if warnings:
        result += f"\nNOT FOUND: {', '.join(warnings)}"
    return result
