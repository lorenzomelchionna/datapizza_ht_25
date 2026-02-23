"""License Checker Agent: verifies chef licenses and technique requirements."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_FAST
from hackapizza_solution.prompts.license_checker import SYSTEM_PROMPT
from hackapizza_solution.tools.license_tools import (
    get_chefs_with_license,
    get_required_licenses_for_technique,
)
from hackapizza_solution.tools.menu_tools import get_chef_info


def create_agent() -> Agent:
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_FAST,
    )
    return Agent(
        name="license_checker",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_chefs_with_license,
            get_required_licenses_for_technique,
            get_chef_info,
        ],
    )
