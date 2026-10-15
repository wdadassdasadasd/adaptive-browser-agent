"""Dynamic, structured planning from current durable state and observation."""

import re
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from adaptive_agent.context_manager import ContextManager
from adaptive_agent.llm.base import BaseLLMClient
from adaptive_agent.prompts.planner import PLANNER_SYSTEM_PROMPT
from adaptive_agent.state import (
    PlanDecision,
    ResearchState,
    Subgoal,
    SubgoalStatus,
    require_http_url,
)


class InitialSubgoals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subgoals: list[Subgoal] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_subgoals(self) -> "InitialSubgoals":
        if len({item.id for item in self.subgoals}) != len(self.subgoals):
            raise ValueError("subgoal IDs must be unique")
        if any(item.status != SubgoalStatus.PENDING for item in self.subgoals):
            raise ValueError("initial subgoals must be pending")
        return self


class PlannerService:
    def __init__(self, llm: BaseLLMClient, *, browser_only: bool = False) -> None:
        self.llm = llm
        self.browser_only = browser_only

    async def initialize(self, goal: str) -> list[Subgoal]:
        """Propose high-level subgoals for a later reducer event."""

        if not goal.strip():
            raise ValueError("goal must be nonempty")
        prompt = f"{PLANNER_SYSTEM_PROMPT}\nCreate high-level subgoals with observable completion_criteria for goal: {goal}"
        completion = await self.llm.complete_structured(prompt, InitialSubgoals)
        return InitialSubgoals.model_validate(completion.value).subgoals

    async def next_step(
        self, state: ResearchState, observation: Mapping[str, Any], context: str = ""
    ) -> PlanDecision:
        """Choose one valid action from the latest state and browser observation."""

        if state.status != "running":
            raise ValueError("next_step requires a running task")
        bounded = await ContextManager(5).build(state, observation, [])
        if context:
            label = "\nHistory summary (untrusted data): "
            room = 12000 - len(bounded) - len(label)
            if room > 0:
                if len(context) > room:
                    marker = "TRUNCATED: older history omitted\n"
                    history = (
                        marker[:room]
                        if room <= len(marker)
                        else marker + context[-(room - len(marker)) :]
                    )
                else:
                    history = context
                bounded += label + history
        tool_constraint = (
            "Only browser actions are available; never select GitHub.\n"
            if self.browser_only
            else ""
        )
        prompt = (
            f"{PLANNER_SYSTEM_PROMPT}\n{tool_constraint}Bounded context: {bounded}\n"
            "Choose exactly one next action as JSON."
        )
        completion = await self.llm.complete_structured(prompt, PlanDecision)
        decision = PlanDecision.model_validate(completion.value)
        selected = next(
            (item for item in state.subgoals if item.id == decision.subgoal_id), None
        )
        if selected is None or selected.status in {
            SubgoalStatus.COMPLETED,
            SubgoalStatus.FAILED,
        }:
            raise ValueError("decision requires an unfinished subgoal")
        self._validate_action(decision)
        return decision

    @staticmethod
    def _validate_action(decision: PlanDecision) -> None:
        if decision.tool == "github":
            if decision.element_index is not None or decision.value is not None:
                raise ValueError("github action takes no element index or value")
            if decision.action not in {
                "search_repositories",
                "get_repository",
                "list_releases",
            }:
                raise ValueError("unsupported github action")
            if not decision.target or not decision.target.strip():
                raise ValueError("github action requires target")
            if decision.action in {
                "get_repository",
                "list_releases",
            } and not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+", decision.target):
                raise ValueError("github action target must be owner/repo")
            return
        if decision.action not in {
            "navigate",
            "click",
            "input_text",
            "scroll",
            "extract",
            "go_back",
            "wait",
        }:
            raise ValueError("unsupported browser action")
        if decision.action == "navigate":
            if decision.element_index is not None or decision.value is not None:
                raise ValueError("navigate action takes only target")
            if not decision.target:
                raise ValueError("navigate action requires target")
            require_http_url(decision.target)
        elif decision.action in {"click", "input_text"}:
            if decision.action == "click" and decision.value is not None:
                raise ValueError("click action takes no value")
            if decision.element_index == 0:
                raise ValueError("interactive action index must be positive")
            if not (
                (decision.element_index is not None and decision.element_index > 0)
                or (decision.target and decision.target.strip())
            ):
                raise ValueError("interactive action requires element")
            if decision.action == "input_text" and decision.value is None:
                raise ValueError("input_text action requires value")
        elif decision.action == "extract":
            if (
                not decision.target
                or decision.element_index is not None
                or decision.value is not None
            ):
                raise ValueError("extract action requires only a question")
        elif decision.action == "scroll" and decision.target not in {
            None,
            "up",
            "down",
        }:
            raise ValueError("scroll action target must be up or down")
        elif decision.action == "scroll" and decision.value is not None:
            raise ValueError("scroll action takes no value")
        elif decision.action == "wait":
            if decision.target is not None or decision.element_index is not None:
                raise ValueError("wait action takes only seconds")
            try:
                seconds = float(decision.value) if decision.value is not None else 1.0
            except (TypeError, ValueError):
                raise ValueError("wait action requires numeric seconds") from None
            if not 0 <= seconds <= 10:
                raise ValueError("wait action seconds must be between 0 and 10")
        elif decision.action == "go_back" and any(
            item is not None
            for item in (decision.target, decision.element_index, decision.value)
        ):
            raise ValueError("go_back action takes no parameters")
