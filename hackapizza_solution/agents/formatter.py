"""Result Formatter Agent: formats final output with dish IDs."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_FAST
from hackapizza_solution.prompts.formatter import SYSTEM_PROMPT
from hackapizza_solution.tools.output_tools import map_dishes_to_ids


def create_agent() -> Agent:
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_FAST,
    )
    return Agent(
        name="result_formatter",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[map_dishes_to_ids],
    )
