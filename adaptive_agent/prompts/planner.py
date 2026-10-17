"""Concise planner contract for DeepSeek JSON output."""

PLANNER_SYSTEM_PROMPT = (
    "Return JSON only. Initialize high-level subgoals with observable completion criteria, "
    "or choose exactly one tool action from the current state and browser observation. "
    "Never produce an up-front action script. Use only unfinished subgoals and supported browser/GitHub actions."
)

PLANNER_ACTION_GUIDE = (
    "Supported actions and target forms: browser has no search action. "
    "Browser: navigate(target: public HTTP(S) URL), click(target: element text or element_index), "
    "input_text(target: element text or element_index, value: text), scroll(target: up/down), "
    "extract(target: question about the current page), go_back, wait. "
    "GitHub: search_repositories(target: query), get_repository(target: owner/repo), "
    "list_releases(target: owner/repo). Use null for unused optional fields. "
    "To search the web with the browser, navigate to a public search URL."
)
