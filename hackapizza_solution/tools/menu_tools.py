"""Tools for searching and filtering the extracted menu data (menus.json)."""

import json
from pathlib import Path

from datapizza.tools import tool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import MENUS_JSON

_menus_cache: list[dict] | None = None


def _load_menus() -> list[dict]:
    global _menus_cache
    if _menus_cache is None:
        _menus_cache = json.loads(MENUS_JSON.read_text(encoding="utf-8"))
    return _menus_cache


@tool
def search_dishes_by_ingredient(ingredient: str) -> str:
    """Find all dishes that contain a specific ingredient. Case-insensitive partial match."""
    menus = _load_menus()
    results = []
    ingredient_lower = ingredient.lower()
    for menu in menus:
        for dish in menu["dishes"]:
            if any(ingredient_lower in ing.lower() for ing in dish["ingredients"]):
                results.append(
                    f"- {dish['name']} (ristorante: {menu['restaurant']}, pianeta: {menu['planet']})"
                )
    if not results:
        return f"Nessun piatto trovato con l'ingrediente '{ingredient}'."
    return f"Piatti con '{ingredient}' ({len(results)} risultati):\n" + "\n".join(results)


@tool
def search_dishes_by_technique(technique: str) -> str:
    """Find all dishes prepared with a specific technique. Case-insensitive partial match."""
    menus = _load_menus()
    results = []
    technique_lower = technique.lower()
    for menu in menus:
        for dish in menu["dishes"]:
            if any(technique_lower in tech.lower() for tech in dish["techniques"]):
                results.append(
                    f"- {dish['name']} (ristorante: {menu['restaurant']}, pianeta: {menu['planet']})"
                )
    if not results:
        return f"Nessun piatto trovato con la tecnica '{technique}'."
    return f"Piatti con tecnica '{technique}' ({len(results)} risultati):\n" + "\n".join(results)


@tool
def filter_dishes_by_restaurant(restaurant: str) -> str:
    """Get all dishes from a specific restaurant. Case-insensitive partial match."""
    menus = _load_menus()
    restaurant_lower = restaurant.lower()
    for menu in menus:
        if restaurant_lower in menu["restaurant"].lower():
            lines = []
            for dish in menu["dishes"]:
                ings = ", ".join(dish["ingredients"])
                techs = ", ".join(dish["techniques"])
                lines.append(f"- {dish['name']}\n  Ingredienti: {ings}\n  Tecniche: {techs}")
            return (
                f"Ristorante: {menu['restaurant']} (pianeta: {menu['planet']})\n"
                f"Chef: {menu['chef']['name']}\n"
                f"Piatti ({len(menu['dishes'])}):\n" + "\n".join(lines)
            )
    return f"Ristorante '{restaurant}' non trovato."


@tool
def filter_dishes_by_planet(planet: str) -> str:
    """Get all dishes served on a specific planet. Case-insensitive match."""
    menus = _load_menus()
    planet_lower = planet.lower()
    results = []
    for menu in menus:
        if planet_lower in menu["planet"].lower():
            for dish in menu["dishes"]:
                results.append(
                    f"- {dish['name']} (ristorante: {menu['restaurant']})"
                )
    if not results:
        return f"Nessun piatto trovato sul pianeta '{planet}'."
    return f"Piatti sul pianeta '{planet}' ({len(results)} risultati):\n" + "\n".join(results)


@tool
def get_chef_info(restaurant: str) -> str:
    """Get chef name and licenses for a restaurant. Case-insensitive partial match."""
    menus = _load_menus()
    restaurant_lower = restaurant.lower()
    for menu in menus:
        if restaurant_lower in menu["restaurant"].lower():
            chef = menu["chef"]
            licenses_str = ", ".join(f"{k}: {v}" for k, v in chef["licenses"].items())
            return (
                f"Ristorante: {menu['restaurant']} (pianeta: {menu['planet']})\n"
                f"Chef: {chef['name']}\n"
                f"Licenze: {licenses_str}"
            )
    return f"Chef non trovato per ristorante '{restaurant}'."


@tool
def get_all_dishes_with_details() -> str:
    """Get a complete dump of all dishes with ingredients and techniques.
    Use only for complex cross-cutting queries that need full data."""
    menus = _load_menus()
    lines = []
    for menu in menus:
        lines.append(f"\n=== {menu['restaurant']} ({menu['planet']}) - Chef: {menu['chef']['name']} ===")
        for dish in menu["dishes"]:
            ings = ", ".join(dish["ingredients"])
            techs = ", ".join(dish["techniques"])
            lines.append(f"  {dish['name']}")
            lines.append(f"    Ingredienti: {ings}")
            lines.append(f"    Tecniche: {techs}")
    return "\n".join(lines)
