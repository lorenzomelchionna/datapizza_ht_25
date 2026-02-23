"""Order Expert Agent: expert on the 3 professional Orders and their rules."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_STRONG
from hackapizza_solution.prompts.order_expert import SYSTEM_PROMPT
from hackapizza_solution.tools.rag_tools import (
    query_codice_galattico,
    query_manuale_cucina,
)


def create_agent() -> Agent:
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_STRONG,
    )
    return Agent(
        name="order_expert",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[query_codice_galattico, query_manuale_cucina],
    )
