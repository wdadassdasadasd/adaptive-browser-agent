"""Observe -> Plan -> Act -> Evaluate -> Replan orchestration boundary."""

from adaptive_agent.context_manager import ContextManager
from adaptive_agent.evaluator import EvaluatorService
from adaptive_agent.planner import PlannerService
from adaptive_agent.reporter import ReporterService
from adaptive_agent.state import ResearchReport
from adaptive_agent.state_reducer import StateReducer
from adaptive_agent.tools.router import ToolRouter


class AgentLoop:
    def __init__(
        self,
        planner: PlannerService,
        evaluator: EvaluatorService,
        reducer: StateReducer,
        context_manager: ContextManager,
        tool_router: ToolRouter,
        reporter: ReporterService,
        max_steps: int,
    ) -> None:
        self.planner = planner
        self.evaluator = evaluator
        self.reducer = reducer
        self.context_manager = context_manager
        self.tool_router = tool_router
        self.reporter = reporter
        self.max_steps = max_steps

    async def run(self, goal: str) -> ResearchReport:
        """Run one research task once the V1 orchestration is implemented."""

        raise NotImplementedError("TODO(V1): implement the adaptive research loop")
