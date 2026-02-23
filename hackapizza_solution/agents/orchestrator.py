"""Orchestrator Agent: classifies questions and delegates to specialized agents."""

import sys
from pathlib import Path

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import OPENAI_API_KEY, MODEL_FAST
from hackapizza_solution.prompts.orchestrator import SYSTEM_PROMPT
from hackapizza_solution.tools.classifier_tool import classify_question

from hackapizza_solution.agents.menu_search import create_agent as create_menu_search
from hackapizza_solution.agents.manual_expert import create_agent as create_manual_expert
from hackapizza_solution.agents.license_checker import create_agent as create_license_checker
from hackapizza_solution.agents.distance_calculator import create_agent as create_distance_calculator
from hackapizza_solution.agents.order_expert import create_agent as create_order_expert
from hackapizza_solution.agents.compliance_checker import create_agent as create_compliance_checker
from hackapizza_solution.agents.formatter import create_agent as create_formatter


def create_orchestrator() -> Agent:
    """Create the orchestrator agent with can_call() to all sub-agents."""
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_FAST,
    )

    menu_search_agent = create_menu_search()
    manual_expert_agent = create_manual_expert()
    license_checker_agent = create_license_checker()
    distance_calculator_agent = create_distance_calculator()
    order_expert_agent = create_order_expert()
    compliance_checker_agent = create_compliance_checker()
    formatter_agent = create_formatter()

    orchestrator = Agent(
        name="orchestrator",
        client=client,
        system_prompt=SYSTEM_PROMPT,
        tools=[classify_question],
        stateless=False,
    )

    orchestrator.can_call([
        menu_search_agent,
        manual_expert_agent,
        license_checker_agent,
        distance_calculator_agent,
        order_expert_agent,
        compliance_checker_agent,
        formatter_agent,
    ])

    return orchestrator
