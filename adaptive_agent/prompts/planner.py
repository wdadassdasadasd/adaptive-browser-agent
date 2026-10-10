"""Concise planner contract for DeepSeek JSON output."""

PLANNER_SYSTEM_PROMPT = (
    "Return JSON only. Initialize high-level subgoals with observable completion criteria, "
    "or choose exactly one tool action from the current state and browser observation. "
    "Never produce an up-front action script. Use only unfinished subgoals and supported browser/GitHub actions."
)
