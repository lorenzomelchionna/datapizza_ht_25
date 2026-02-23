"""Extract ingredient percentages from the two blogpost HTML reviews.

The blogposts contain exact percentage information for regulated ingredients
used in specific dishes. This data is crucial for compliance checking (Cat. K).

Usage:
    cd <project_root>
    ./pizza_env/bin/python -m hackapizza_solution.data_preparation.parse_blogposts
"""

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import BLOGPOST_PCT_JSON, DATA_DIR

# Manually extracted from the two blogpost HTML files.
# blog_etere_del_gusto.html (reviewer: Cassandra Stellaris, restaurant: L'Etere del Gusto, Pandora)
# blog_sapore_del_dune.html (reviewer: Marco Stellaris, restaurant: Sapore del Dune)

BLOGPOST_PERCENTAGES: dict[str, dict[str, float]] = {
    # --- Blog: L'Etere del Gusto ---
    "Il Risveglio del Drago Celeste": {
        "Carne di Drago": 8.0,
    },
    "Cosmic Harmony Infusion": {
        "Petali di Eco": 3.0,
    },
    "Sinfonia Multiversale in Otto Movimenti": {
        "Muffa Lunare": 2.0,
    },
    # --- Blog: Sapore del Dune ---
    "Sinfonia Quantistica delle Stelle": {
        "Sale Temporale": 1.0,
        "Nettare di Sirena": 0.1,
    },
    "Galassia di Sapore Quantico": {
        "Polvere di Stelle": 1.0,
        "Carne di Drago": 1.0,
    },
    "Evanescenza Quantica": {
        "Cristalli di Memoria": 0.1,
        "Petali di Eco": 0.1,
    },
    "Pioggia di Dimensioni Galattiche": {
        "Essenza di Vuoto": 3.0,
        "Nettare di Sirena": 0.1,
    },
    "Sinfonia Galattica": {
        "Funghi dell'Etere": 2.0,
        "Carne di Drago": 2.0,
    },
}


def run():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    BLOGPOST_PCT_JSON.write_text(
        json.dumps(BLOGPOST_PERCENTAGES, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {len(BLOGPOST_PERCENTAGES)} dishes to {BLOGPOST_PCT_JSON}")
    for dish, ings in sorted(BLOGPOST_PERCENTAGES.items()):
        print(f"  {dish}: {ings}")


if __name__ == "__main__":
    run()
