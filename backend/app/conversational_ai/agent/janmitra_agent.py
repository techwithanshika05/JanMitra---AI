import asyncio

from app.conversational_ai.conversation.orchestrator import ConversationOrchestrator
from app.conversational_ai.persistence.models import VoiceSession
from app.conversational_ai.persistence.repository import VoiceRepository
from app.conversational_ai.prompts import SYSTEM_PROMPT
from app.database import SessionLocal


def build_agent(room_name: str):
    from livekit.agents import Agent, ChatContext, ChatMessage, StopResponse

    class JanMitraAgent(Agent):
        def __init__(self) -> None:
            super().__init__(instructions=SYSTEM_PROMPT)

        async def on_user_turn_completed(
            self, turn_ctx: ChatContext, new_message: ChatMessage
        ) -> None:
            query = new_message.text_content.strip()
            if not query:
                return

            def ground_turn() -> str:
                db = SessionLocal()
                try:
                    session = db.query(VoiceSession).filter(
                        VoiceSession.room_name == room_name
                    ).first()
                    if session is None:
                        return (
                            "Session persistence is unavailable. Do not provide a "
                            "factual answer; ask the citizen to use text support."
                        )
                    repo = VoiceRepository(db)
                    repo.add_turn(
                        session.id,
                        speaker="user",
                        text=query,
                        language=session.current_language,
                    )
                    reply = ConversationOrchestrator(db).respond(
                        query, session.current_language
                    )
                    session.current_language = reply.language
                    repo.add_turn(
                        session.id,
                        speaker="agent",
                        text=reply.text,
                        language=reply.language,
                        intent=reply.intent,
                        answer_mode=reply.answer_mode,
                        evidence_status=reply.evidence_status,
                        confidence=reply.confidence,
                        sources=reply.sources,
                    )
                    db.commit()
                    return reply.text
                except Exception:
                    db.rollback()
                    return (
                        "सत्यापित जानकारी सेवा अभी उपलब्ध नहीं है। कृपया आधिकारिक "
                        "पोर्टल, हेल्पलाइन, सीएससी या स्थानीय कार्यालय से पुष्टि करें।"
                    )
                finally:
                    db.close()

            grounded_response = await asyncio.to_thread(ground_turn)

            # ConversationOrchestrator already produced the final grounded answer.
            # Send it directly to TTS instead of asking the Sarvam LLM to rewrite it.
            chat_ctx = self.chat_ctx.copy()
            chat_ctx.add_message(role="user", content=query)
            await self.update_chat_ctx(chat_ctx)
            self.session.say(
                grounded_response,
                allow_interruptions=True,
                add_to_chat_ctx=True,
            )
            raise StopResponse

    return JanMitraAgent()
