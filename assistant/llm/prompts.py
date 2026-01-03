from textwrap import dedent
from typing import Iterable, Sequence


def build_system_prompt(base: str, reflections: Iterable[str]) -> str:
    reflection_text = "\n".join(f"- {r}" for r in reflections)
    prompt = dedent(
        f"""
        {base}

        Kendine düzenli olarak şu soruyu sor: "Mustafa için nasıl daha faydalı olabilirim?".
        Bu yansımayı kullanıcıya aynen söyleme; içsel düşün ve sadece faydalı sonuçları yanıtına yedir.
        Refleksiyonlar:
        {reflection_text if reflection_text else '- (henüz yok)'}
        """
    ).strip()
    return prompt


def build_user_prompt(
    user_input: str,
    working_memory: Sequence[str],
    retrieved_memories: Sequence[str],
    procedural_rules: Sequence[str],
    cognee_snippets: Sequence[str] | None = None,
) -> str:
    working_text = "\n".join(f"- {m}" for m in working_memory) if working_memory else "- (yok)"
    retrieved_text = (
        "\n".join(f"- {m}" for m in retrieved_memories) if retrieved_memories else "- (yok)"
    )
    procedural_text = (
        "\n".join(f"- {r}" for r in procedural_rules) if procedural_rules else "- (yok)"
    )
    cognee_text = (
        "\n".join(f"- {c}" for c in (cognee_snippets or [])) if cognee_snippets else "- (yok)"
    )
    return dedent(
        f"""
        Kullanıcı girdisi: {user_input}

        Çalışma Hafızası (son mesajlar):
        {working_text}

        Geri Çağrılan Anılar (epizodik/semantik/temporal):
        {retrieved_text}

        Prosedürel Hafıza (kurallar/yetenekler):
        {procedural_text}

        Cognee / Graph İlişkileri:
        {cognee_text}

        Görev: Türkçe, kısa ve içten yanıt ver. Gerekirse Mustafa hakkında bildiklerini kullan.
        """
    ).strip()
