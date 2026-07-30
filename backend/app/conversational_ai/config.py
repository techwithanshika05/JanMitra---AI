from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class VoiceSettings:
    livekit_url: str = settings.LIVEKIT_URL
    livekit_api_key: str = settings.LIVEKIT_API_KEY
    livekit_api_secret: str = settings.LIVEKIT_API_SECRET
    sarvam_api_key: str = settings.SARVAM_API_KEY
    agent_name: str = settings.VOICE_AGENT_NAME
    default_language: str = settings.VOICE_DEFAULT_LANGUAGE
    stt_model: str = settings.SARVAM_STT_MODEL
    stt_mode: str = settings.SARVAM_STT_MODE
    tts_model: str = settings.SARVAM_TTS_MODEL
    tts_speaker: str = settings.SARVAM_TTS_SPEAKER.strip().lower()
    tts_pace: float = settings.SARVAM_TTS_PACE
    llm_model: str = settings.SARVAM_LLM_MODEL
    room_ttl_minutes: int = settings.VOICE_ROOM_TTL_MINUTES

    @property
    def livekit_ready(self) -> bool:
        return bool(self.livekit_url and self.livekit_api_key and self.livekit_api_secret)

    @property
    def sarvam_ready(self) -> bool:
        return bool(self.sarvam_api_key)


voice_settings = VoiceSettings()
