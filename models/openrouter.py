"""OpenRouter provider for open-weight and other routed models in ABFINI V0.1.

The model is selected at runtime through OPENROUTER_MODEL. This keeps the
ABFINI router independent from any single open-weight model family.
"""
import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .provider import GenerationRequest, GenerationResult

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3-30b-a3b"


class OpenRouterProviderError(RuntimeError):
    """Raised when OpenRouter cannot produce a valid answer."""


@dataclass
class OpenRouterProvider:
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    timeout: float = 60.0
    opener: Callable[..., object] = urlopen

    @classmethod
    def from_env(cls) -> "OpenRouterProvider":
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        return cls(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
            base_url=os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {
                    "role": "user",
                    "content": f"Contexte:\n{request.context}\n\nQuestion:\n{request.question}",
                },
            ],
            "stream": False,
        }
        http_request = Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/aronadiop2303-ai/ABFINI",
                "X-Title": "ABFINI",
            },
            method="POST",
        )
        try:
            with self.opener(http_request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenRouterProviderError(f"OpenRouter request failed: {exc}") from exc

        try:
            data = json.loads(raw)
            answer = data["choices"][0]["message"]["content"]
            response_model = data.get("model", self.model)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise OpenRouterProviderError("OpenRouter returned an invalid response") from exc

        if not isinstance(answer, str) or not answer.strip():
            raise OpenRouterProviderError("OpenRouter returned an empty answer")
        return GenerationResult(answer=answer.strip(), model=str(response_model))
