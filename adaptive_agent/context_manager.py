"""Deterministic bounded context for a single planning decision."""

import json
from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any

from adaptive_agent.events import AgentEvent
from adaptive_agent.state import ResearchState

_LIMIT = 12000


class ContextManager:
    def __init__(self, recent_trace_count: int) -> None:
        if not 1 <= recent_trace_count <= 5:
            raise ValueError("recent_trace_count must be between 1 and 5")
        self.recent_trace_count = recent_trace_count

    async def build(
        self,
        state: ResearchState,
        observation: Mapping[str, Any],
        recent_traces: Sequence[AgentEvent],
    ) -> str:
        """Keep current evidence and the last traces without growing with task age."""

        truncated = False

        def clip(value: object, length: int) -> str:
            nonlocal truncated
            rendered = str(value)
            if len(rendered) > length:
                truncated = True
                return rendered[:length] + "…"
            return rendered

        def clip_dom(value: object, length: int) -> str:
            nonlocal truncated
            rendered = str(value)
            if len(rendered) > length:
                truncated = True
                head = (length - 1) // 2
                return rendered[:head] + "…" + rendered[-(length - head - 1) :]
            return rendered

        selected = next(
            (item for item in state.subgoals if item.id == state.current_subgoal_id),
            None,
        )
        if (
            len(state.subgoals) > 8
            or len(state.facts) > 8
            or len(state.visited_urls) > 8
            or len(state.search_history) > 8
        ):
            truncated = True
        if len(recent_traces) > self.recent_trace_count:
            truncated = True
        failed_actions: deque[dict[str, str]] = deque(maxlen=5)
        for event in recent_traces:
            result = event.payload.get("tool_result")
            decision = event.payload.get("decision")
            if (
                isinstance(result, dict)
                and result.get("success") is False
                and isinstance(decision, dict)
            ):
                failed_actions.append(
                    {
                        "tool": clip(decision.get("tool", ""), 30),
                        "action": clip(decision.get("action", ""), 50),
                        "target": clip(decision.get("target", ""), 180),
                        "error_type": clip(result.get("error_type", ""), 30),
                        "error_message": clip(result.get("error_message", ""), 180),
                    }
                )
        observation_view = {}
        priority = (
            "url",
            "title",
            "dom_state",
            "recent_events",
            "state_error",
            "browser_errors",
            "text",
            "content",
        )
        observation_keys = [key for key in priority if key in observation]
        observation_keys.extend(
            key for key in observation if key not in priority and key != "screenshot"
        )
        for key in observation_keys[:8]:
            value = observation[key]
            if key == "dom_state":
                representation = getattr(value, "llm_representation", None)
                if callable(representation):
                    value = representation()
            limit = (
                5000
                if key == "dom_state"
                else 500
                if key in {"text", "content"} and "dom_state" in observation
                else 3000
                if key in {"text", "content"}
                else 1000
                if key == "recent_events"
                else 500
            )
            observation_view[clip(key, 100)] = (
                clip_dom(value, limit) if key == "dom_state" else clip(value, limit)
            )
        if len(observation_keys) > 8:
            truncated = True
        traces = list(recent_traces)[-self.recent_trace_count :]
        payload = {
            "goal": clip(state.goal, 500),
            "step": state.step,
            "current_subgoal_id": clip(state.current_subgoal_id, 100)
            if state.current_subgoal_id
            else None,
            "completed_subgoals": [
                clip(item.id, 100)
                for item in state.subgoals
                if item.status == "completed"
            ][-5:],
            "current_subgoal": (
                {
                    "id": clip(selected.id, 100),
                    "status": selected.status,
                    "description": clip(selected.description, 250),
                    "completion_criteria": clip(selected.completion_criteria, 250),
                    "failure_reason": clip(selected.failure_reason, 150)
                    if selected.failure_reason
                    else None,
                }
                if selected
                else None
            ),
            "subgoals": [
                {
                    "id": clip(item.id, 100),
                    "status": item.status,
                    "description": clip(item.description, 180),
                }
                for item in state.subgoals[-8:]
            ],
            "facts": [
                {
                    "content": clip(item.content, 250),
                    "source_url": clip(item.source_url, 300),
                    "source_title": clip(item.source_title, 100),
                }
                for item in state.facts[-8:]
            ],
            "visited_urls": [clip(url, 200) for url in state.visited_urls[-8:]],
            "search_history": [clip(query, 200) for query in state.search_history[-8:]],
            "counts": {
                "facts": len(state.facts),
                "visited_urls": len(state.visited_urls),
                "searches": len(state.search_history),
                "traces": len(recent_traces),
            },
            "observation": observation_view,
            "recent_traces": [],
            "failed_actions": list(failed_actions),
        }
        for item in traces:
            summary = {
                "step": item.step,
                "event_type": item.event_type,
                "message": clip(item.message, 250),
            }
            decision = item.payload.get("decision")
            if isinstance(decision, dict):
                summary["decision"] = {
                    "tool": clip(decision.get("tool", ""), 30),
                    "action": clip(decision.get("action", ""), 50),
                    "target": clip(decision.get("target", ""), 180),
                    "element_index": decision.get("element_index"),
                }
            result = item.payload.get("tool_result")
            if isinstance(result, dict):
                summary["tool_result"] = {
                    "success": result.get("success"),
                    "error_type": clip(result.get("error_type", ""), 30),
                    "source_url": clip(result.get("source_url", ""), 200),
                }
            evaluation = item.payload.get("evaluation")
            if isinstance(evaluation, dict):
                summary["evaluation"] = {
                    "success": evaluation.get("success"),
                    "subgoal_completed": evaluation.get("subgoal_completed"),
                    "error_type": clip(evaluation.get("error_type", ""), 30),
                    "reason": clip(evaluation.get("reason", ""), 150),
                }
            payload["recent_traces"].append(summary)
        rendered = json.dumps(payload, ensure_ascii=False, default=str)
        if truncated or len(rendered) > _LIMIT:
            payload["truncation"] = "TRUNCATED: older or long history omitted"
            rendered = json.dumps(payload, ensure_ascii=False, default=str)
        for key, keep in (
            ("visited_urls", 0),
            ("search_history", 0),
            ("subgoals", 0),
            ("completed_subgoals", 0),
            ("facts", 1),
            ("failed_actions", 1),
        ):
            while len(rendered) > _LIMIT and len(payload[key]) > keep:
                payload[key].pop(0)
                rendered = json.dumps(payload, ensure_ascii=False, default=str)
        if len(rendered) > _LIMIT:
            for key, limit in (
                ("content", 100),
                ("text", 100),
                ("browser_errors", 100),
                ("state_error", 100),
                ("title", 200),
                ("url", 200),
                ("recent_events", 300),
                ("dom_state", 3000),
            ):
                if key not in payload["observation"]:
                    continue
                value = payload["observation"][key]
                payload["observation"][key] = (
                    clip_dom(value, limit) if key == "dom_state" else clip(value, limit)
                )
                rendered = json.dumps(payload, ensure_ascii=False, default=str)
                if len(rendered) <= _LIMIT:
                    break
        if len(rendered) > _LIMIT:
            payload = {
                key: payload[key]
                for key in (
                    "goal",
                    "step",
                    "current_subgoal",
                    "facts",
                    "observation",
                    "recent_traces",
                    "failed_actions",
                    "truncation",
                )
            }
            rendered = json.dumps(payload, ensure_ascii=False, default=str)
        return rendered
