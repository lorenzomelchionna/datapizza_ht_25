"""Compliance Checker Agent: verifies dishes against Codice Galattico limits."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_STRONG
from hackapizza_solution.prompts.compliance_checker import SYSTEM_PROMPT
from hackapizza_solution.tools.compliance_tools import (
    get_ingredient_percentages,
    get_substance_limits,
)
from hackapizza_solution.tools.rag_tools import query_codice_galattico


def create_agent() -> Agent:
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_STRONG,
    )
    return Agent(
        name="compliance_checker",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_ingredient_percentages,
            get_substance_limits,
            query_codice_galattico,
        ],
    )
