"""Tools for calculating distances between planets using Distanze.csv."""

import csv
from pathlib import Path

from datapizza.tools import tool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import DISTANZE_CSV

_distances_cache: dict[str, dict[str, float]] | None = None


def _load_distances() -> dict[str, dict[str, float]]:
    global _distances_cache
    if _distances_cache is None:
        _distances_cache = {}
        with open(DISTANZE_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                planet = row["/"]
                _distances_cache[planet] = {
                    k: float(v) for k, v in row.items() if k != "/"
                }
    return _distances_cache


@tool
def get_planets_within_radius(origin: str, radius: float) -> str:
    """Get all planets within a given radius (in light-years) from the origin planet.
    Includes the origin planet itself (distance 0)."""
    distances = _load_distances()
    if origin not in distances:
        return f"Planet '{origin}' not found. Valid planets: {', '.join(distances.keys())}"
    nearby = []
    for planet, dist in distances[origin].items():
        if dist <= radius:
            nearby.append((planet, dist))
    nearby.sort(key=lambda x: x[1])
    lines = [f"- {planet} ({dist:.0f} light-years)" for planet, dist in nearby]
    return (
        f"Planets within {radius} light-years from {origin} ({len(nearby)} results):\n"
        + "\n".join(lines)
    )


@tool
def get_distance(planet_a: str, planet_b: str) -> str:
    """Get the distance in light-years between two planets."""
    distances = _load_distances()
    if planet_a not in distances:
        return f"Planet '{planet_a}' not found."
    if planet_b not in distances[planet_a]:
        return f"Planet '{planet_b}' not found."
    dist = distances[planet_a][planet_b]
    return f"Distance between {planet_a} and {planet_b}: {dist:.0f} light-years"
