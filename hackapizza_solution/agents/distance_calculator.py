"""Distance Calculator Agent: computes distances between planets."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_FAST
from hackapizza_solution.prompts.distance_calculator import SYSTEM_PROMPT
from hackapizza_solution.tools.distance_tools import (
    get_planets_within_radius,
    get_distance,
)


def create_agent() -> Agent:
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_FAST,
    )
    return Agent(
        name="distance_calculator",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_planets_within_radius, get_distance],
    )
