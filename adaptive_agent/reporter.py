"""Final report generation boundary."""

from adaptive_agent.state import ResearchReport, ResearchState


class ReporterService:
    async def generate(self, state: ResearchState) -> ResearchReport:
        """Generate a final report without attaching it to ResearchState."""

        raise NotImplementedError(
            "TODO(V1): generate a research report from durable facts"
        )
