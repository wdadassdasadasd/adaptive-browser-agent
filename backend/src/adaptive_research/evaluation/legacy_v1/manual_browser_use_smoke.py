"""Run the preserved browser-use baseline as an opt-in manual smoke check."""

import asyncio

from browser_use import Agent, ChatOpenAI
from dotenv import load_dotenv

BASELINE_TASK = (
    "打开 GitHub，搜索 browser-use/browser-use 仓库，并告诉我这个仓库是做什么的。"
)


async def main() -> None:
    load_dotenv()
    agent = Agent(
        task=BASELINE_TASK,
        llm=ChatOpenAI(model="gpt-4.1-mini"),
    )
    history = await agent.run()

    print("最终结果：")
    print(history.final_result())


if __name__ == "__main__":
    asyncio.run(main())
