import logging
from pathlib import Path
from typing import Iterable

from assistant.config.schemas import Settings
from assistant.llm.clients import BaseLLMClient, LLMResponse, build_client
from assistant.llm.prompts import build_system_prompt, build_user_prompt
from assistant.memory.embedding import EmbeddingBackend, build_embedding
from assistant.memory.store import MemoryStore
from assistant.memory.temporal import choose_temporal_truth, decay_confidence, format_memory_snippet
from assistant.memory.cognee import build_cognee_client, DummyCogneeClient
from assistant.services.profiling import ReflectionTracker
from assistant.typing import MemoryKind

logger = logging.getLogger(__name__)


class ConversationEngine:
    def __init__(
        self,
        settings: Settings,
        llm_client: BaseLLMClient | None = None,
        embedding_backend: EmbeddingBackend | None = None,
        db_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self.memory_store = MemoryStore(db_path or settings.paths.db_file)
        self.llm_client = llm_client or build_client(
            provider=settings.llm.provider,
            base_url=settings.llm.base_url,
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
        )
        self.embedding = embedding_backend or build_embedding(
            backend=settings.embedding.backend,
            model_name=settings.embedding.model_name,
            device=settings.embedding.device,
            base_url=settings.embedding.base_url,
        )
        # Cognee stub (future integration)
        cognee_cfg = getattr(settings, "cognee", {}) or {}
        self.cognee = build_cognee_client(
            enabled=cognee_cfg.get("enabled", False), endpoint=cognee_cfg.get("endpoint")
        )
        self.reflections = ReflectionTracker(refresh_turns=settings.profile.refresh_turns)

    def ingest_memory(
        self,
        kind: MemoryKind,
        content: str,
        source: str,
        confidence: float = 0.6,
        topic: str | None = None,
    ) -> int:
        embedding = self.embedding.embed(content)
        return self.memory_store.add_memory(
            kind=kind,
            content=content,
            embedding=embedding,
            source=source,
            confidence=confidence,
            topic=topic,
        )

    def retrieve_context(self, query: str) -> list[str]:
        query_vec = self.embedding.embed(query)
        kinds: Iterable[MemoryKind] = ["episodic", "semantic", "temporal_truth"]
        results = self.memory_store.topk_similar(
            query_embedding=query_vec,
            kinds=kinds,
            top_k=self.settings.memory.top_k,
            min_similarity=self.settings.memory.min_similarity,
            decay_halflife_days=self.settings.memory.decay_halflife_days,
        )
        snippets = [format_memory_snippet(mem) for mem, _score in results]
        return snippets

    def _working_memory(self) -> list[str]:
        msgs = self.memory_store.last_messages(limit=self.settings.working.window)
        return [f"{role}: {content}" for role, content in msgs]

    def _update_temporal_truth(self, content: str, topic: str | None) -> None:
        if not topic:
            return
        existing = self.memory_store.list_memories(["temporal_truth"])
        same_topic = [m for m in existing if m.get("topic") == topic]
        new_conf = 0.8
        for mem in same_topic:
            decayed = decay_confidence(
                confidence=mem["confidence"],
                created_at=mem["created_at"],
                half_life_days=self.settings.memory.decay_halflife_days,
            )
            mem["confidence"] = decayed
        self.ingest_memory(
            kind="temporal_truth",
            content=content,
            source="conversation",
            confidence=new_conf,
            topic=topic,
        )

    def chat(self, user_input: str) -> LLMResponse:
        logger.info("User input: %s", user_input)
        self.memory_store.add_message(role="user", content=user_input)
        context_snippets = self.retrieve_context(user_input)
        working_memory = self._working_memory()
        procedural_rules = self.settings.procedural.rules or []
        cognee_snippets: list[str] = []
        try:
            cognee_snippets = self.cognee.query(user_input, top_k=self.settings.memory.top_k)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover - optional path
            logger.debug("Cognee query skipped: %s", exc)
        reflections = self.reflections.reflections or []
        system_prompt = build_system_prompt(self.settings.ui.system_prompt, reflections)
        user_prompt = build_user_prompt(
            user_input=user_input,
            working_memory=working_memory,
            retrieved_memories=context_snippets,
            procedural_rules=procedural_rules,
            cognee_snippets=cognee_snippets,
        )
        response = self.llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stream=self.settings.ui.stream,
        )
        self.memory_store.add_message(role="assistant", content=response.content)
        self.ingest_memory(
            kind="episodic",
            content=f"Kullanıcı: {user_input}\nAsistan: {response.content}",
            source="conversation",
            confidence=0.6,
        )
        self._update_temporal_truth(content=user_input, topic=self.settings.memory.temporal_truth_key)
        self.reflections.maybe_add_reflection("Kullanıcıyla daha derin bağ kurma önerisi üret")
        return response

    def profile_summary(self) -> str:
        memories = self.memory_store.list_memories(["episodic", "semantic", "temporal_truth"])
        chosen = choose_temporal_truth(memories)
        lines = ["Temporal hafıza özetleri:"]
        lines.extend(format_memory_snippet(mem) for mem in chosen[:5])
        return "\n".join(lines)
