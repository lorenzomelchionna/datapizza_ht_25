"""Menu Search Agent: searches and filters dishes from the extracted menu data."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_FAST
from hackapizza_solution.prompts.menu_search import SYSTEM_PROMPT
from hackapizza_solution.tools.menu_tools import (
    search_dishes_by_ingredient,
    search_dishes_by_technique,
    filter_dishes_by_restaurant,
    filter_dishes_by_planet,
    get_chef_info,
    get_all_dishes_with_details,
)


def create_agent() -> Agent:
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_FAST,
    )
    return Agent(
        name="menu_search",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            search_dishes_by_ingredient,
            search_dishes_by_technique,
            filter_dishes_by_restaurant,
            filter_dishes_by_planet,
            get_chef_info,
            get_all_dishes_with_details,
        ],
    )
