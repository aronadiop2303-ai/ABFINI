"""OpenAI-compatible provider for local/self-hosted open models in ABFINI V0.1.

Works with vLLM, Ollama-compatible gateways, llama.cpp servers, TGI gateways,
and other endpoints exposing a compatible /chat/completions API.
"""
import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .provider import GenerationRequest, GenerationResult

DEFAULT_BASE_URL = "http://localhost:8000/v1/chat/completions"
DEFAULT_MODEL = "local-model"


class OpenCompatibleProviderError(RuntimeError):
    """Raised when an OpenAI-compatible endpoint cannot produce an answer."""


@dataclass
class OpenCompatibleProvider:
    api_key: str = ""
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    timeout: float = 60.0
    opener: Callable[..., object] = urlopen

    @classmethod
    def from_env(cls) -> "OpenCompatibleProvider":
        return cls(
            api_key=os.getenv("OPEN_MODEL_API_KEY", "").strip(),
            model=os.getenv("OPEN_MODEL_NAME", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
            base_url=os.getenv("OPEN_MODEL_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
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
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        http_request = Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with self.opener(http_request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenCompatibleProviderError(f"open-compatible request failed: {exc}") from exc

        try:
            data = json.loads(raw)
            answer = data["choices"][0]["message"]["content"]
            response_model = data.get("model", self.model)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise OpenCompatibleProviderError("open-compatible endpoint returned an invalid response") from exc

        if not isinstance(answer, str) or not answer.strip():
            raise OpenCompatibleProviderError("open-compatible endpoint returned an empty answer")
        return GenerationResult(answer=answer.strip(), model=str(response_model))
