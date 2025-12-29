from textwrap import dedent
from typing import Iterable


def build_system_prompt(base: str, reflections: Iterable[str]) -> str:
    reflection_text = "\n".join(f"- {r}" for r in reflections)
    prompt = dedent(
        f"""
        {base}

        Kendine düzenli olarak şu soruyu sor: "Mustafa için nasıl daha faydalı olabilirim?".
        Eğer ilgiliyse yeni öneriler üret.
        Refleksiyonlar:
        {reflection_text if reflection_text else '- (henüz yok)'}
        """
    ).strip()
    return prompt


def build_user_prompt(user_input: str, memory_snippets: list[str]) -> str:
    memories = "\n".join(f"- {m}" for m in memory_snippets)
    return dedent(
        f"""
        Kullanıcı girdisi: {user_input}
        İlgili anılar:
        {memories if memories else '- (anı bulunamadı)'}
        Görev: Türkçe, kısa ve içten yanıt ver. Gerekirse Mustafa hakkında bildiklerini kullan.
        """
    ).strip()
