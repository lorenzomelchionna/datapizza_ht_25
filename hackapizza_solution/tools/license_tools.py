"""Tools for checking chef licenses and technique requirements."""

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
def get_chefs_with_license(license_type: str, min_grade: int) -> str:
    """Find all chefs who have at least the specified grade for a license type.
    License codes: P=Psionica, t=Temporale, G=Gravitazionale, e+=Antimateria,
    Mx=Magnetica, Q=Quantistica, c=Luce, LTK=LTK."""
    menus = _load_menus()
    results = []
    for menu in menus:
        chef = menu["chef"]
        grade = chef["licenses"].get(license_type, 0)
        if grade >= min_grade:
            results.append(
                f"- {chef['name']} ({menu['restaurant']}, {menu['planet']}) - {license_type}: {grade}"
            )
    if not results:
        return f"Nessun chef trovato con licenza {license_type} >= grado {min_grade}."
    return (
        f"Chef con licenza {license_type} >= grado {min_grade} ({len(results)} risultati):\n"
        + "\n".join(results)
    )


@tool
def get_required_licenses_for_technique(technique: str) -> str:
    """Look up which licenses are required to use a specific cooking technique.
    This information comes from the Codice Galattico and Manuale di Cucina.
    Returns a description of the requirements that should be verified against chef licenses."""
    return (
        f"Per determinare le licenze richieste per la tecnica '{technique}', "
        f"consulta il Codice Galattico (sezione sulle tecniche regolamentate) e il "
        f"Manuale di Cucina di Sirius Cosmo (sezione sulle licenze per categoria). "
        f"Le tecniche di ogni categoria richiedono licenze specifiche con un grado minimo. "
        f"Usa l'agente Manual Expert o Order Expert con RAG per ottenere i dettagli esatti."
    )
