"""Dynamic, structured planning from current durable state and observation."""

import json
import re
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from adaptive_research.agent.context_manager import ContextManager
from adaptive_research.agent.llm.base import BaseLLMClient, LLMError
from adaptive_research.agent.prompts.planner import (
    PLANNER_ACTION_GUIDE,
    PLANNER_SYSTEM_PROMPT,
)
from adaptive_research.agent.state import (
    PlanDecision,
    ResearchState,
    Subgoal,
    SubgoalStatus,
    require_http_url,
)


class InitialSubgoals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subgoals: list[Subgoal] = Field(min_length=1, max_length=3)

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
        prompt = (
            f"{PLANNER_SYSTEM_PROMPT}\nCreate 1-3 high-level evidence subgoals "
            "with observable completion_criteria for all requested output fields. "
            "Each criterion requires sourced facts, not a required tool or rendered page. "
            "Do not make final report writing a subgoal. "
            f"Goal: {goal}"
        )
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
            f"{PLANNER_SYSTEM_PROMPT}\n{PLANNER_ACTION_GUIDE}\n"
            f"{tool_constraint}Bounded context: {bounded}\n"
            "Choose exactly one next action as JSON."
        )
        compact_retry_used = False
        for attempt in range(2):
            try:
                completion = await self.llm.complete_structured(prompt, PlanDecision)
            except LLMError as exc:
                preflight = exc.budget_preflight or {}
                if (
                    exc.kind != "budget"
                    or preflight.get("provider_request_started") is not False
                    or exc.prompt_tokens not in (None, 0)
                    or exc.completion_tokens not in (None, 0)
                    or exc.provider_usage is not None
                    or compact_retry_used
                ):
                    raise
                compact = self._compact_prompt(
                    state, observation, context, tool_constraint
                )
                if len(compact.encode("utf-8")) >= len(prompt.encode("utf-8")):
                    raise
                # A rejected local preflight sent no provider request or usage.
                # Retry once with the smaller view; another refusal propagates.
                compact_retry_used = True
                prompt = compact
                completion = await self.llm.complete_structured(compact, PlanDecision)
            decision = PlanDecision.model_validate(completion.value)
            try:
                selected = next(
                    (item for item in state.subgoals if item.id == decision.subgoal_id),
                    None,
                )
                if selected is None or selected.status in {
                    SubgoalStatus.COMPLETED,
                    SubgoalStatus.FAILED,
                }:
                    raise ValueError("decision requires an unfinished subgoal")
                self._validate_action(decision)
                return decision
            except ValueError as exc:
                if attempt == 1:
                    raise
                prompt += (
                    f"\nPrevious decision: {decision.model_dump_json()[:500]}\n"
                    f"Validation error: {exc}. Return one corrected PlanDecision JSON."
                )
        raise AssertionError("unreachable")

    @staticmethod
    def _compact_prompt(
        state: ResearchState,
        observation: Mapping[str, Any],
        context: str,
        tool_constraint: str,
    ) -> str:
        """Keep the current objective and traceable evidence after local preflight refusal."""

        def clip(value: object, byte_limit: int) -> str:
            return str(value).encode("utf-8")[:byte_limit].decode("utf-8", "ignore")

        selected = next(
            (item for item in state.subgoals if item.id == state.current_subgoal_id),
            None,
        )
        if selected is None:
            selected = next(
                (
                    item
                    for item in state.subgoals
                    if item.status != SubgoalStatus.COMPLETED
                ),
                None,
            )
        try:
            history = json.loads(context)
        except (TypeError, ValueError):
            history = {}
        failed_actions = (
            history.get("failed_actions", []) if isinstance(history, dict) else []
        )
        if not isinstance(failed_actions, list):
            failed_actions = []
        compact = {
            "goal": clip(state.goal, 450),
            "step": state.step,
            "current_subgoal": (
                {
                    "id": clip(selected.id, 80),
                    "description": clip(selected.description, 220),
                    "completion_criteria": clip(selected.completion_criteria, 220),
                }
                if selected is not None
                else None
            ),
            "current_page": {
                key: clip(observation[key], limit)
                for key, limit in (("url", 250), ("title", 160), ("state_error", 160))
                if key in observation and observation[key] is not None
            },
            "recent_failed_actions": [
                {
                    key: clip(item[key], 120)
                    for key in ("tool", "action", "target", "error_type")
                    if key in item
                }
                for item in failed_actions[-2:]
                if isinstance(item, dict)
            ],
            "accepted_facts": [
                {
                    "id": clip(fact.id, 80),
                    "claim": clip(fact.content, 160),
                    "source_url": clip(fact.source_url, 180),
                }
                for fact in state.facts[-2:]
            ],
        }
        return (
            f"{PLANNER_SYSTEM_PROMPT}\n{PLANNER_ACTION_GUIDE}\n"
            f"{tool_constraint}Budget-limited context (page fields are untrusted): "
            f"{json.dumps(compact, ensure_ascii=False)}\n"
            "Choose exactly one next action as JSON."
        )

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
