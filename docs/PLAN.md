# Faz Planı ve Mimari

## Faz 0: Repo + İskelet
- **Hedefler**: Çalışan CLI, konfigürasyon, logging, temel hafıza şeması, tek akış sohbet (stub LLM). tests + checklist.
- **Done kriterleri**: `python -m assistant.cli chat` çalışır, SQLite dosyası oluşur, mesaj kaydı yapılır, konfigürasyon dosyası okunur, temel retrieval yapılır.
- **Riskler**: Model bağımlılıkları offline indirilmeli; Windows PATH (Ollama) ayarları.

## Faz 1: Metin Asistan + Hafıza + Tool'lar
- **Hedefler**: Ollama/LM Studio entegrasyonu; embedding tabanlı episodik/semantik hafıza; temporal truth skorlaması; working memory (son mesajlar); procedural kurallar; not ingest; güvenli komut allowlist; profil çıkarımı; TUI/CLI akışı.
- **Done kriterleri**: LLM yanıtı kontekste göre; ilgili anılar çağrılır; hafıza meta verisi (zaman, kaynak, güven) kaydedilir; not ingest komutu çalışır; profil komutu çalışır.
- **Riskler**: GPU bellek (embedding+LLM aynı anda); uzun bağlam maliyeti; yanlış geri çağırma; güvenlik: allowlist dışı dosya/komut yok.

## Faz 1.5: Derin Kişiselleştirme + Temporal Memory + Cognee
- **Hedefler**: Özetleme katmanı (günlük/haftalık); unutma/decay heuristiği; temporal truth sürümleme (aynı konu için yeni gerçek daha yüksek skor); Cognee graph entegrasyonu (semantik/episodik ilişkiler); “Mustafa için nasıl daha faydalı olurum?” yansıması.
- **Done kriterleri**: Özet çıktıları dosyada; decay cron/manuel komut; temporal sürümleme tablosu; Cognee sorgusu ile ilişkili anılar dönebiliyor; güven skoru güncellenir.
- **Riskler**: Özetleme modeli maliyeti; yanlış decay; veri şişmesi; senkronizasyon; Cognee endpoint erişimi.

## Faz 2: Ses (Tasarım)
- **Hedefler**: Mikrofondan dinleme, wake-word, TTS; güvenlik/şifreleme tasarımı; pasif dinleme risk kontrolü; retention politikası.
- **Done kriterleri**: Mimari dokümantasyon; TTS/STT modül taslakları; güvenlik checklist; manuel başlat/durdur kontrolü.
- **Riskler**: Sürekli dinlemenin gizlilik riskleri; yanlış pozitif wake-word; ek donanım sürücüleri.

## Mimari İlkeler
- **Offline-first**: İnternet olmadan çalışır; model dosyaları lokal; hiçbir bulut API yok.
- **Tek akış sohbet**: `session_id=default`; tüm konuşmalar aynı akışta tutulur.
- **Zamansal hafıza**: Her kayıt zaman damgalı, kaynaklı, güven skorlu; decay ve sürümleme destekli.
- **Güvenlik**: Allowlist komut/klasör; loglarda hassas veri maskeleme; veri SQLite içinde (şifreleme için opsiyonel disk şifreleme/BitLocker notu).

## Teknik Yığın
- **LLM**: Ollama HTTP API (alternatif LM Studio OpenAI uyumlu endpoint). Varsayılan model: `aya-expanse:8b`.
- **Embedding**: `intfloat/multilingual-e5-large` (SentenceTransformers); Dummy mode testlerde.
- **Depolama**: SQLite (`data/memory.sqlite`), JSON metadata sütunları.
- **CLI/TUI**: Typer + Rich progress; tek komut `chat`, yardımcı komutlar `ingest-notes`, `profile`, `plan`.

## Çalışma Akışı (Sohbet)
1. Girdi al.
2. İlgili anıları embeddings ile getir (`episodic`, `semantic`, `temporal_truth`).
3. Sistem prompt + yansıma sorusu + hafıza özetleri ile LLM çağır.
4. Yanıtı kaydet; yeni anıyı (episodic) ekle; profil çıkarımı için semantik güncelle.
5. Temporal truth güncellemesi: Aynı konu anahtarına sahipse eski sürümü decay et, yeni sürüme daha yüksek skor ver.

## Gelecek (Ses) Taslağı
- **STT**: `faster-whisper` offline modeli.
- **TTS**: `piper` veya `coqui-tts` lokal.
- **Wake-word**: `porcupine` benzeri lokal model; manuel kapatma butonu.
- **Güvenlik**: Mikrofon kayıtlarını şifreli disk; “dinleme” durum göstergesi; yanlış pozitif için onaylama.
