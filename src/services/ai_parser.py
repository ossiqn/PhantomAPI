import json
from typing import Any

from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError

from src.core.exceptions import (
    OpenAIAuthError,
    OpenAIRateLimitError,
    OpenAIConnectionError,
    PhantomAPIException,
)
from src.utils.logger import setup_logger


logger = setup_logger("PhantomAPI.AIParser")


_SYSTEM_PROMPT = """
You are PhantomAPI's precision data extraction engine.

Rules you must follow without exception:
1. Read the PAGE CONTENT and the EXTRACTION PROMPT carefully.
2. Extract ONLY the data the prompt requests.
3. Return the result as a single, valid JSON object.
4. NEVER include markdown, code fences, explanations, or extra text.
5. If the requested data is not found, return: {"result": null, "reason": "Data not found in page content."}
6. Structure the JSON logically based on the extraction prompt.
"""


class AIParserService:

    def _build_messages(self, content: str, prompt: str) -> list[dict[str, str]]:
        user_message = (
            f"EXTRACTION PROMPT:\n{prompt}\n\n"
            f"PAGE CONTENT:\n{content}"
        )

        return [
            {"role": "system", "content": _SYSTEM_PROMPT.strip()},
            {"role": "user",   "content": user_message},
        ]

    def parse(
        self,
        content: str,
        prompt:  str,
        api_key: str,
    ) -> tuple[dict[str, Any], int]:
        client = OpenAI(api_key=api_key)

        try:
            logger.info("Sending content to OpenAI gpt-4o for extraction...")

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=self._build_messages(content, prompt),
                temperature=0.0,
                response_format={"type": "json_object"},
            )

        except AuthenticationError:
            raise OpenAIAuthError()

        except RateLimitError:
            raise OpenAIRateLimitError()

        except APIConnectionError:
            raise OpenAIConnectionError()

        except Exception as exc:
            raise PhantomAPIException(
                status_code=500,
                error="Unexpected OpenAI API error.",
                detail=str(exc),
            )

        raw_output  = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        try:
            extracted = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            logger.error(f"OpenAI returned invalid JSON: {exc}")
            raise PhantomAPIException(
                status_code=500,
                error="AI model returned malformed JSON.",
                detail="Try rephrasing your extraction prompt.",
            )

        logger.info(
            f"Extraction complete. "
            f"Tokens used: {tokens_used} | "
            f"Keys returned: {list(extracted.keys())}"
        )

        return extracted, tokens_used


ai_parser_service = AIParserService()