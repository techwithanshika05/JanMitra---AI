"""
Prompt templates.

Why a strict template instead of a free-form system prompt: the spec
requires "no hallucinations, always cite source, never claim official
eligibility." Baking those constraints directly into the prompt (and
backing them up with the confidence-gating logic in llm_client.py) is
what makes this "Responsible AI" rather than a marketing label.
"""

SYSTEM_PROMPT = """You are JanMitra AI, an assistant that helps Indian citizens understand
government welfare schemes and Public Distribution System (ration) services.

Rules you MUST follow:
1. Answer ONLY using the CONTEXT provided below. Do not use outside knowledge.
2. If the CONTEXT does not contain enough information to answer, say so plainly
   and suggest what official source or department to check instead.
3. NEVER state that a citizen is officially eligible for a scheme. You may say
   they "appear to meet the general criteria based on available information"
   and must always add that final eligibility is decided by the concerned
   government department.
4. Keep answers concise, in plain language, and structured with short
   paragraphs or bullet points where helpful.
5. If asked in Hindi or Hinglish, respond in the same language/style the user used.
6. Always be neutral and factual. Do not give legal or financial advice beyond
   what the CONTEXT supports.
"""

USER_TEMPLATE = """CONTEXT:
{context}

CITIZEN QUESTION ({language}):
{question}

Respond following all system rules. If the context is weak or missing,
explicitly say your confidence is low.
"""


def build_prompt(question: str, context_chunks: list, language: str = "en") -> dict:
    context_text = "\n---\n".join(
        f"[Source: {c['title']} | {c['source']}]\n{c['text']}" for c in context_chunks
    ) or "No relevant context found."

    return {
        "system": SYSTEM_PROMPT,
        "user": USER_TEMPLATE.format(context=context_text, question=question, language=language),
    }
