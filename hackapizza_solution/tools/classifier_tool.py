"""Wraps question_classifier.py as a datapizza @tool for the orchestrator."""

import sys
from pathlib import Path

from datapizza.tools import tool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from question_classifier import classify, CATEGORIES


@tool
def classify_question(question: str) -> str:
    """Classify a hackathon question into categories (A-L) with confidence scores.
    Returns the categories, their descriptions, confidence scores, and required data sources."""
    result = classify(question, use_embeddings=False)
    lines = []
    for code in sorted(result.categories, key=lambda c: -result.categories[c]):
        cat = CATEGORIES[code]
        score = result.categories[code]
        sources = ", ".join(cat.data_sources)
        lines.append(
            f"  {code} ({score:.0%}): {cat.name} - {cat.description_it} [Fonti: {sources}]"
        )
    composite = "COMPOSITA" if result.is_composite else "SINGOLA"
    header = f"Classificazione: {composite}\nCategorie rilevate:"
    return header + "\n" + "\n".join(lines)
