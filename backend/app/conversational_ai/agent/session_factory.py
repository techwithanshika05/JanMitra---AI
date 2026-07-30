from app.conversational_ai.config import voice_settings
from livekit.plugins import sarvam


def build_agent_session():
    """Build the current LiveKit 1.x STT-LLM-TTS pipeline.

    The Sarvam plugin is imported at module load time so LiveKit registers it
    on the worker's main thread before any job runner starts.
    """
    from livekit.agents import AgentSession

    if not voice_settings.sarvam_ready:
        raise RuntimeError("SARVAM_API_KEY is not configured")
    return AgentSession(
        stt=sarvam.STT(language="hi-IN", model=voice_settings.stt_model, mode=voice_settings.stt_mode),
        llm=sarvam.LLM(model=voice_settings.llm_model),
        tts=sarvam.TTS(
            target_language_code="hi-IN", model=voice_settings.tts_model,
            speaker=voice_settings.tts_speaker, pace=voice_settings.tts_pace,
            temperature=0.6, output_audio_bitrate="128k",
        ),
        turn_handling={
            "endpointing": {
                "mode": "fixed",
                "min_delay": 0.3,
                "max_delay": 1.0,
            },
            # Start LLM preparation while the turn detector confirms that the
            # citizen has finished, but never synthesize unvalidated speech.
            "preemptive_generation": {
                "enabled": False,
                "preemptive_tts": False,
            },
        },
    )
