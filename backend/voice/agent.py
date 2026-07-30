"""
Step 1: Echo voice agent.

Confirms mic -> STT -> LLM -> TTS -> speaker pipeline works,
before RAG is wired in (Step 2).
"""

import logging
from dotenv import load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import sarvam

load_dotenv()

logger = logging.getLogger("voice-agent")


class EchoAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "Repeat back exactly what the user said, in the same "
                "language, with no extra commentary. This is a pipeline test."
            )
        )


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        stt=sarvam.STT(language="en-IN", flush_signal=True),
        llm=sarvam.LLM(model="sarvam-30b"),
        tts=sarvam.TTS(target_language_code="en-IN", speaker="pooja"),
        turn_detection="stt",
        min_endpointing_delay=0.07,
    )

    await session.start(agent=EchoAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="janmitra-voice-agent"))