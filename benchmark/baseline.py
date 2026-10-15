"""Checked-out browser-use baseline, with no project Agent policy."""

import asyncio
from typing import Any

from benchmark.metrics import url_visit_transitions


class _TokenBudgetStop(Exception):
    """Abort upstream before it can make a post-step judge request."""


async def run_baseline(task: str, *, agent_factory: Any = None) -> dict[str, Any]:
    """Run upstream Agent; retain partial history on timeout or failure."""
    if agent_factory is None:
        from browser_use import Agent, ChatDeepSeek

        agent_factory = lambda prompt: Agent(
            task=prompt, llm=ChatDeepSeek(model="deepseek-flash")
        )
    agent = agent_factory(task)
    error = None
    budget_breached = False
    history = None
    observed_usage = None
    post_step_observations: list[tuple[int, str | None]] = []

    async def enforce_tokens(current_agent: Any) -> None:
        nonlocal budget_breached
        session = getattr(current_agent, "browser_session", None)
        if session is not None:
            history_count = len(current_agent.history.history)
            try:
                post_step_observations.append(
                    (history_count, await session.get_current_page_url())
                )
            except Exception:  # noqa: BLE001 - URL telemetry must not abort research
                post_step_observations.append((history_count, None))
        usage = await current_agent.token_cost_service.get_usage_summary()
        if usage.entry_count and usage.total_tokens >= 40_000:
            budget_breached = True
            current_agent.stop()
            raise _TokenBudgetStop

    try:
        history = await asyncio.wait_for(
            agent.run(max_steps=30, on_step_end=enforce_tokens), timeout=900
        )
    except TimeoutError:
        history = agent.history
        error = "time_limit"
    except _TokenBudgetStop:
        history = agent.history
    except Exception as exc:  # noqa: BLE001 - preserve failed attempts
        history = getattr(agent, "history", None)
        error = type(exc).__name__
    finally:
        if history is None or not getattr(history, "usage", None):
            service = getattr(agent, "token_cost_service", None)
            if service is not None:
                try:
                    observed_usage = await service.get_usage_summary()
                except Exception:  # noqa: BLE001 - an interrupted run may lack usage
                    observed_usage = None
        try:
            await agent.close()
        except Exception as exc:  # noqa: BLE001 - keep the partial history
            error = error or f"cleanup_{type(exc).__name__}"
    if history is None:
        prompt_tokens = (
            observed_usage.total_prompt_tokens
            if observed_usage and observed_usage.entry_count
            else None
        )
        completion_tokens = (
            observed_usage.total_completion_tokens
            if observed_usage and observed_usage.entry_count
            else None
        )
        return {
            "answer": "",
            "urls": [],
            "trace": [],
            "steps": 0,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "status": "failed",
            "failure_reason": "token_budget_breach"
            if prompt_tokens is not None
            and completion_tokens is not None
            and prompt_tokens + completion_tokens > 40_000
            else error or "missing_history",
            "budget_parity": "mismatched",
        }
    usage = history.usage or observed_usage
    prompt_tokens = usage.total_prompt_tokens if usage and usage.entry_count else None
    completion_tokens = (
        usage.total_completion_tokens if usage and usage.entry_count else None
    )
    steps = len(history.history)
    if history.history:
        last = history.history[-1]
        results = getattr(last, "result", None) or []
        if (
            getattr(last, "model_output", object()) is None
            and len(results) == 1
            and getattr(results[0], "error", None)
            == "Failed to complete task in maximum steps"
        ):
            steps -= 1
            error = error or "step_budget_reached"
    if (
        prompt_tokens is not None
        and completion_tokens is not None
        and prompt_tokens + completion_tokens > 40_000
    ):
        error = "token_budget_breach"
    elif budget_breached and error is None and history.is_successful() is not True:
        error = "token_budget_reached"
    if steps > 30:
        error = "step_budget_breach"
    is_done = getattr(history, "is_done", None)
    if error is None and callable(is_done) and not is_done():
        error = "upstream_unfinished"
    upstream_success = history.is_successful()
    trace = []
    for index, item in enumerate(history.history):
        actions = []
        output = getattr(item, "model_output", None)
        for action in getattr(output, "action", []) if output else []:
            actions.extend(action.model_dump(exclude_none=True).keys())
        trace.append({"step": index + 1, "actions": actions})
    visited_urls: list[str | None] = []
    pre_step_urls = history.urls()
    next_pre_step = 0
    for history_count, post_url in post_step_observations:
        while next_pre_step < min(history_count, len(pre_step_urls)):
            visited_urls.append(pre_step_urls[next_pre_step])
            next_pre_step += 1
        visited_urls.append(post_url)
    visited_urls.extend(pre_step_urls[next_pre_step:])
    return {
        "answer": history.final_result() or "",
        "urls": url_visit_transitions(visited_urls),
        "trace": trace,
        "steps": steps,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "status": "completed" if error is None else "failed",
        "failure_reason": error,
        "upstream_success": upstream_success,
        # Upstream exposes aggregate usage after run, so cap parity cannot be enforced.
        "budget_parity": "mismatched",
    }
