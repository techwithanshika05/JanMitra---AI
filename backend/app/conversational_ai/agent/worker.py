"""Run with: python -m app.conversational_ai.agent.worker dev"""
from app.conversational_ai.agent.janmitra_agent import build_agent
from app.conversational_ai.agent.session_factory import build_agent_session
from app.conversational_ai.config import voice_settings
from app.conversational_ai.prompts.system_prompt import HINDI_GREETING


async def entrypoint(ctx):
    await ctx.connect()
    session = build_agent_session()
    await session.start(room=ctx.room, agent=build_agent(ctx.room.name))
    # The greeting is fixed copy, so send it straight to TTS. Routing it
    # through the 105B LLM adds several seconds without changing the message.
    await session.say(HINDI_GREETING, allow_interruptions=True)


def main() -> None:
    from livekit.agents import AgentServer, cli

    # Keep one ready job process in development as well as production so the
    # first caller does not wait for Windows to spawn a cold process.
    server = AgentServer(num_idle_processes=1)
    server.rtc_session(entrypoint, agent_name=voice_settings.agent_name)
    cli.run_app(server)


if __name__ == "__main__":
    main()
