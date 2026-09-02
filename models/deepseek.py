"""DeepSeek text-generation provider for ABFINI V0.1.

Uses the native DeepSeek Chat Completions HTTP API without storing secrets
in the repository. The API key must be supplied at runtime.
"""
import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .provider import GenerationRequest, GenerationResult

DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-pro"


class DeepSeekProviderError(RuntimeError):
    """Raised when the DeepSeek API cannot produce a valid answer."""


@dataclass
class DeepSeekProvider:
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    timeout: float = 60.0
    opener: Callable[..., object] = urlopen

    @classmethod
    def from_env(cls) -> "DeepSeekProvider":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        return cls(
            api_key=api_key,
            model=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
            base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
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
            "thinking": {"type": "disabled"},
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        http_request = Request(
            self.base_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self.opener(http_request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise DeepSeekProviderError(f"DeepSeek request failed: {exc}") from exc

        try:
            data = json.loads(raw)
            answer = data["choices"][0]["message"]["content"]
            response_model = data.get("model", self.model)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise DeepSeekProviderError("DeepSeek returned an invalid response") from exc

        if not isinstance(answer, str) or not answer.strip():
            raise DeepSeekProviderError("DeepSeek returned an empty answer")
        return GenerationResult(answer=answer.strip(), model=str(response_model))
