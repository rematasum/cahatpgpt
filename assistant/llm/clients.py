import logging
from dataclasses import dataclass
from typing import Iterable, Optional


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str


class BaseLLMClient:
    def generate(self, system_prompt: str, user_prompt: str, stream: bool = False) -> LLMResponse:
        raise NotImplementedError


class DummyLLMClient(BaseLLMClient):
    def __init__(self) -> None:
        self.history: list[str] = []

    def generate(self, system_prompt: str, user_prompt: str, stream: bool = False) -> LLMResponse:
        logger.debug("Using DummyLLMClient")
        text = "(Dummy yanıt) " + user_prompt[:200]
        self.history.append(text)
        return LLMResponse(content=text)


class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: str, model: str, temperature: float, max_tokens: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, system_prompt: str, user_prompt: str, stream: bool = False) -> LLMResponse:
        requests = _require_requests()
        url = f"{self.base_url}/api/generate"
        prompt = f"<|system|>{system_prompt}<|user|>{user_prompt}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "options": {"num_predict": self.max_tokens},
            "stream": stream,
        }
        logger.info("Calling Ollama model=%s", self.model)
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        if stream:
            content_parts: list[str] = []
            for line in resp.iter_lines():
                if not line:
                    continue
                data = line.decode("utf-8")
                content_parts.append(data)
            text = "".join(content_parts)
        else:
            data = resp.json()
            text = data.get("response", "")
        return LLMResponse(content=text)


class LMStudioClient(BaseLLMClient):
    def __init__(self, base_url: str, model: str, temperature: float, max_tokens: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, system_prompt: str, user_prompt: str, stream: bool = False) -> LLMResponse:
        requests = _require_requests()
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }
        logger.info("Calling LM Studio model=%s", self.model)
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        if stream:
            content_parts: list[str] = []
            for line in resp.iter_lines():
                if not line:
                    continue
                content_parts.append(line.decode("utf-8"))
            text = "".join(content_parts)
        else:
            data = resp.json()
            choices = data.get("choices", [])
            text = choices[0]["message"]["content"] if choices else ""
        return LLMResponse(content=text)


def build_client(provider: str, base_url: str, model: str, temperature: float, max_tokens: int) -> BaseLLMClient:
    if provider == "ollama":
        return OllamaClient(base_url, model, temperature, max_tokens)
    if provider == "lmstudio":
        return LMStudioClient(base_url, model, temperature, max_tokens)
    return DummyLLMClient()


def _require_requests():
    try:
        import requests  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - optional path
        raise RuntimeError("requests kütüphanesi kurulu değil. requirements.txt'i yükleyin.") from exc
    return requests
