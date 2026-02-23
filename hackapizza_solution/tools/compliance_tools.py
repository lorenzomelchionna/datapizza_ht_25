"""Tools for checking ingredient compliance with Codice Galattico limits."""

import json
from pathlib import Path

from datapizza.tools import tool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import BLOGPOST_PCT_JSON

_pct_cache: dict[str, dict[str, float]] | None = None


def _load_percentages() -> dict[str, dict[str, float]]:
    global _pct_cache
    if _pct_cache is None:
        _pct_cache = json.loads(BLOGPOST_PCT_JSON.read_text(encoding="utf-8"))
    return _pct_cache


@tool
def get_ingredient_percentages(dish_name: str) -> str:
    """Get the ingredient percentages for a dish as reported in blogpost reviews.
    Only available for dishes reviewed in the two blogposts.
    Returns ingredient names and their volume percentages."""
    pct = _load_percentages()
    if dish_name in pct:
        lines = [f"- {ing}: {val}%" for ing, val in pct[dish_name].items()]
        return f"Percentuali ingredienti per '{dish_name}':\n" + "\n".join(lines)
    # Try partial match
    for name, ings in pct.items():
        if dish_name.lower() in name.lower() or name.lower() in dish_name.lower():
            lines = [f"- {ing}: {val}%" for ing, val in ings.items()]
            return f"Percentuali ingredienti per '{name}':\n" + "\n".join(lines)
    return (
        f"Nessuna percentuale disponibile per '{dish_name}'. "
        f"Piatti con dati disponibili: {', '.join(pct.keys())}"
    )


@tool
def get_substance_limits(substance: str) -> str:
    """Look up the legal limits for a regulated substance from the Codice Galattico.
    Returns a description of how to check compliance. The actual coefficients and
    formulas must be retrieved via RAG on the codice_galattico collection."""
    return (
        f"Per verificare i limiti legali di '{substance}', consulta il Codice Galattico:\n"
        f"1. Trova il coefficiente della sostanza (CRP, IPM, IBX, ecc.)\n"
        f"2. Applica la formula: se coefficiente > soglia, la % massima consentita è limitata\n"
        f"3. Confronta con la percentuale effettiva del piatto (dai blogpost)\n"
        f"Usa l'agente Compliance con RAG sulla collection 'codice_galattico' per i valori esatti."
    )
