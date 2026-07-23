"""
llm_client.py

Groq LLM client for the JanMitra RAG system.

This module is responsible ONLY for communicating with
the Groq API.

Responsibilities:
- Load Groq configuration from environment variables.
- Initialize the Groq client.
- Send system and user prompts to Groq.
- Generate responses.
- Handle API and configuration errors.
- Return clean generated text.

This module DOES NOT:
- Process PDFs.
- Generate embeddings.
- Search ChromaDB.
- Retrieve document chunks.
- Build RAG context.
- Build JanMitra prompts.

Prompt construction is handled by:

    rag/prompt_builder.py

Complete RAG flow:

User Question
    ->
QueryProcessor
    ->
Retriever
    ->
ContextBuilder
    ->
PromptBuilder
    ->
LLMClient
    ->
Groq API
    ->
Final Answer
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError as exc:
    raise ImportError(
        "The 'groq' package is not installed. "
        "Install it using: pip install groq"
    ) from exc


# ============================================================
# Load Environment Variables
# ============================================================

load_dotenv()


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# Custom Exceptions
# ============================================================

class LLMClientError(Exception):
    """
    Base exception for all LLM client errors.
    """


class LLMConfigurationError(LLMClientError):
    """
    Raised when Groq configuration is missing or invalid.
    """


class LLMConnectionError(LLMClientError):
    """
    Raised when communication with the Groq API fails.
    """


class LLMGenerationError(LLMClientError):
    """
    Raised when Groq does not return a valid response.
    """


# ============================================================
# LLM Client
# ============================================================

class LLMClient:
    """
    Low-level Groq API client for JanMitra.

    This class receives already-built prompts from
    PromptBuilder and sends them to Groq.

    Example:

        client = LLMClient()

        answer = client.generate(
            prompt="Explain the scheme.",
            system_prompt="Answer clearly and concisely."
        )

        print(answer)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Initialize Groq LLM client.

        Args:
            api_key:
                Optional Groq API key.
                Defaults to GROQ_API_KEY from .env.

            model:
                Optional Groq model ID.
                Defaults to GROQ_MODEL from .env.

            temperature:
                Default generation temperature.

            max_tokens:
                Default maximum output tokens.

            timeout:
                API request timeout in seconds.
        """

        # ----------------------------------------------------
        # API Key
        # ----------------------------------------------------

        self.api_key = (
            api_key
            or os.getenv(
                "GROQ_API_KEY"
            )
        )

        if not self.api_key:

            raise LLMConfigurationError(
                "GROQ_API_KEY is not configured.\n\n"
                "Add your Groq API key to backend/.env:\n\n"
                "GROQ_API_KEY=gsk_your_api_key_here"
            )

        # ----------------------------------------------------
        # Model
        # ----------------------------------------------------

        self.model = (
            model
            or os.getenv(
                "GROQ_MODEL",
                "llama-3.3-70b-versatile",
            )
        )

        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        if temperature is None:

            temperature = float(
                os.getenv(
                    "GROQ_TEMPERATURE",
                    "0.1",
                )
            )

        self.temperature = temperature

        # ----------------------------------------------------
        # Maximum Output Tokens
        # ----------------------------------------------------

        if max_tokens is None:

            max_tokens = int(
                os.getenv(
                    "GROQ_MAX_TOKENS",
                    "500",
                )
            )

        self.max_tokens = max_tokens

        # ----------------------------------------------------
        # Timeout
        # ----------------------------------------------------

        if timeout is None:

            timeout = float(
                os.getenv(
                    "GROQ_TIMEOUT",
                    "120",
                )
            )

        self.timeout = timeout

        # ----------------------------------------------------
        # Validate Configuration
        # ----------------------------------------------------

        if not self.model.strip():

            raise LLMConfigurationError(
                "GROQ_MODEL cannot be empty."
            )

        if not 0 <= self.temperature <= 2:

            raise LLMConfigurationError(
                "temperature must be between 0 and 2."
            )

        if self.max_tokens <= 0:

            raise LLMConfigurationError(
                "max_tokens must be greater than 0."
            )

        if self.timeout <= 0:

            raise LLMConfigurationError(
                "timeout must be greater than 0."
            )

        # ----------------------------------------------------
        # Initialize Groq Client
        # ----------------------------------------------------

        try:

            self.client = Groq(
                api_key=self.api_key,
                timeout=self.timeout,
            )

        except Exception as exc:

            logger.exception(
                "Failed to initialize Groq client."
            )

            raise LLMConfigurationError(
                f"Failed to initialize Groq client: {exc}"
            ) from exc

        logger.info(
            "Groq LLMClient initialized | "
            "model=%s | temperature=%s | "
            "max_tokens=%s",
            self.model,
            self.temperature,
            self.max_tokens,
        )

    # ========================================================
    # Main Generation Method
    # ========================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response using the Groq API.

        This is the main method that should be called by
        rag_pipeline.py.

        Args:
            prompt:
                User prompt generated by PromptBuilder.

            system_prompt:
                System prompt generated by PromptBuilder.

            temperature:
                Optional temperature override.

            max_tokens:
                Optional maximum output token override.

        Returns:
            Clean generated text.

        Example:

            answer = client.generate(
                prompt=built_prompt.user_prompt,
                system_prompt=built_prompt.system_prompt,
                temperature=0.1,
                max_tokens=500,
            )
        """

        # ----------------------------------------------------
        # Validate User Prompt
        # ----------------------------------------------------

        if not isinstance(
            prompt,
            str,
        ):

            raise TypeError(
                "prompt must be a string."
            )

        prompt = (
            prompt.strip()
        )

        if not prompt:

            raise ValueError(
                "prompt cannot be empty."
            )

        # ----------------------------------------------------
        # Validate System Prompt
        # ----------------------------------------------------

        if (
            system_prompt is not None
            and not isinstance(
                system_prompt,
                str,
            )
        ):

            raise TypeError(
                "system_prompt must be a string or None."
            )

        if system_prompt:

            system_prompt = (
                system_prompt.strip()
            )

        # ----------------------------------------------------
        # Resolve Generation Settings
        # ----------------------------------------------------

        final_temperature = (
            temperature
            if temperature is not None
            else self.temperature
        )

        final_max_tokens = (
            max_tokens
            if max_tokens is not None
            else self.max_tokens
        )

        if not 0 <= final_temperature <= 2:

            raise ValueError(
                "temperature must be between 0 and 2."
            )

        if final_max_tokens <= 0:

            raise ValueError(
                "max_tokens must be greater than 0."
            )

        # ----------------------------------------------------
        # Build Chat Messages
        # ----------------------------------------------------

        messages: List[
            Dict[str, str]
        ] = []

        if system_prompt:

            messages.append(
                {
                    "role": "system",
                    "content": (
                        system_prompt
                    ),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        # ----------------------------------------------------
        # Log Request
        #
        # Never log the API key or full government document
        # context in production logs.
        # ----------------------------------------------------

        logger.info(
            "Sending generation request to Groq | "
            "model=%s | temperature=%s | "
            "max_tokens=%s",
            self.model,
            final_temperature,
            final_max_tokens,
        )

        # ----------------------------------------------------
        # Send Request to Groq
        # ----------------------------------------------------

        try:

            completion = (
                self.client
                .chat
                .completions
                .create(
                    model=self.model,
                    messages=messages,
                    temperature=(
                        final_temperature
                    ),
                    max_tokens=(
                        final_max_tokens
                    ),
                )
            )

        except Exception as exc:

            logger.exception(
                "Groq API request failed."
            )

            raise LLMConnectionError(
                f"Groq API request failed: {exc}"
            ) from exc

        # ----------------------------------------------------
        # Extract Generated Response
        # ----------------------------------------------------

        try:

            if not completion.choices:

                raise LLMGenerationError(
                    "Groq returned no completion choices."
                )

            generated_text = (
                completion
                .choices[0]
                .message
                .content
            )

        except LLMGenerationError:

            raise

        except (
            AttributeError,
            IndexError,
            TypeError,
        ) as exc:

            logger.exception(
                "Unexpected Groq response format."
            )

            raise LLMGenerationError(
                "Groq returned an unexpected "
                "response format."
            ) from exc

        # ----------------------------------------------------
        # Validate Generated Text
        # ----------------------------------------------------

        if generated_text is None:

            raise LLMGenerationError(
                "Groq returned no generated text."
            )

        generated_text = (
            generated_text.strip()
        )

        if not generated_text:

            raise LLMGenerationError(
                "Groq returned an empty response."
            )

        logger.info(
            "Groq response generated successfully."
        )

        return generated_text

    # ========================================================
    # Generate From BuiltPrompt
    # ========================================================

    def generate_from_prompt(
        self,
        built_prompt: Any,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Convenience method for generating directly from a
        BuiltPrompt object returned by PromptBuilder.

        Expected object attributes:

            built_prompt.system_prompt
            built_prompt.user_prompt

        Example:

            built_prompt = prompt_builder.build(
                question=question,
                context=context,
                language="english",
                query_type="eligibility",
            )

            answer = llm_client.generate_from_prompt(
                built_prompt
            )
        """

        if built_prompt is None:

            raise ValueError(
                "built_prompt cannot be None."
            )

        system_prompt = getattr(
            built_prompt,
            "system_prompt",
            None,
        )

        user_prompt = getattr(
            built_prompt,
            "user_prompt",
            None,
        )

        if not user_prompt:

            raise ValueError(
                "built_prompt must contain "
                "a valid user_prompt."
            )

        return self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # ========================================================
    # Connection Test
    # ========================================================

    def test_connection(
        self,
    ) -> bool:
        """
        Test whether the Groq API connection is working.

        Returns:
            True if Groq responds successfully.
            False otherwise.

        This sends a very small request to the configured
        model.
        """

        logger.info(
            "Testing Groq API connection..."
        )

        try:

            response = self.generate(
                prompt=(
                    "Reply with exactly: OK"
                ),
                system_prompt=(
                    "Follow the user's instruction "
                    "exactly and respond concisely."
                ),
                temperature=0.0,
                max_tokens=10,
            )

            logger.info(
                "Groq connection test response: %s",
                response,
            )

            return True

        except LLMClientError as exc:

            logger.error(
                "Groq connection test failed: %s",
                exc,
            )

            return False

        except Exception as exc:

            logger.exception(
                "Unexpected error during "
                "Groq connection test."
            )

            return False

    # ========================================================
    # Client Information
    # ========================================================

    def get_info(
        self,
    ) -> Dict[str, Any]:
        """
        Return non-sensitive LLM client configuration.

        The API key is intentionally not returned.
        """

        return {
            "provider": "groq",
            "model": self.model,
            "temperature": (
                self.temperature
            ),
            "max_tokens": (
                self.max_tokens
            ),
            "timeout": (
                self.timeout
            ),
        }


# ============================================================
# Manual Test
# ============================================================

def main() -> None:
    """
    Manual test for the Groq LLM client.

    Run from backend directory:

        python -m llm.llm_client

    Required environment variables:

        GROQ_API_KEY=gsk_...

    Optional:

        GROQ_MODEL=llama-3.3-70b-versatile
        GROQ_TEMPERATURE=0.1
        GROQ_MAX_TOKENS=500
        GROQ_TIMEOUT=120
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "JANMITRA - GROQ LLM CLIENT TEST"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Initialize Client
    # --------------------------------------------------------

    try:

        client = LLMClient()

    except LLMConfigurationError as exc:

        print(
            "\nConfiguration Error:"
        )

        print(
            exc
        )

        print(
            "\nCheck your backend/.env file."
        )

        return

    # --------------------------------------------------------
    # Display Configuration
    # --------------------------------------------------------

    info = (
        client.get_info()
    )

    print(
        f"\nProvider: "
        f"{info['provider']}"
    )

    print(
        f"Model: "
        f"{info['model']}"
    )

    print(
        f"Temperature: "
        f"{info['temperature']}"
    )

    print(
        f"Max Tokens: "
        f"{info['max_tokens']}"
    )

    # --------------------------------------------------------
    # Test Connection
    # --------------------------------------------------------

    print(
        "\nTesting Groq connection..."
    )

    if not client.test_connection():

        print(
            "\nGroq API connection failed."
        )

        print(
            "Check your API key, internet connection, "
            "and configured model."
        )

        return

    print(
        "\nGroq API connection successful."
    )

    # --------------------------------------------------------
    # Test Simple Generation
    # --------------------------------------------------------

    print(
        "\nTesting generation..."
    )

    try:

        response = client.generate(
            prompt=(
                "Explain in one sentence what "
                "a government welfare scheme is."
            ),
            system_prompt=(
                "Give only a concise final answer."
            ),
            temperature=0.1,
            max_tokens=100,
        )

        print(
            "\nResponse:"
        )

        print(
            response
        )

    except LLMClientError as exc:

        print(
            "\nGeneration Error:"
        )

        print(
            exc
        )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()