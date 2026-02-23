"""Manual Expert Agent: answers questions about technique categories from the Manuale di Cucina."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_FAST
from hackapizza_solution.prompts.manual_expert import SYSTEM_PROMPT
from hackapizza_solution.tools.rag_tools import query_manuale_cucina


def create_agent() -> Agent:
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_FAST,
    )
    return Agent(
        name="manual_expert",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[query_manuale_cucina],
    )
