# Mustafa'nın Yerel Yapay Zekâ Asistanı

Tamamen çevrimdışı çalışabilen, Windows 11 + RTX 4070 Ti ortamında koşacak kişisel asistan projesi. Varsayılan backend Ollama (alternatif: LM Studio). Hafıza sistemi SQLite tabanlı zamansal bellek, embedding tabanlı anı geri çağırma ve profil çıkarımı sağlar. Tek akış sohbet akışı, terminal tabanlı arayüz ve güvenlik düşünülmüş komut çalıştırma/nota erişim araçları içerir.

## İçindekiler
- [Mimari Plan ve Fazlar](docs/PLAN.md)
- [Checklist](docs/CHECKLIST.md)
- [Kurulum](#kurulum)
- [Çalıştırma](#calistirma)
- [Konfigürasyon](#konfigurasyon)
- [Dosya Ağacı](#dosya-agaci)
- [Testler](#testler)
- [Model Notları](#model-notlari)
 - [Fotoğraf Pipeline Taslağı](#fotograf-pipeline-taslagi)

## Kurulum
Windows 11 + Python 3.10+ varsayılır. İnternet erişimi yoksa gerekli modelleri ve pip paketlerini USB ile aktarın.

1. **Python sanal ortamı**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. **Bağımlılıklar** (önceden indirilmiş wheel klasörü varsa kullanın):
   ```powershell
   pip install --no-index --find-links=.\wheels -r requirements.txt
   ```
   İnternet varsa: `pip install -r requirements.txt`.
3. **Ollama/LM Studio**: Ollama kurulu olmalı ve seçilen modeller lokal olarak pull edilmiş olmalı. İnternet yoksa model dosyalarını USB ile içe aktarın (bkz. [Model Notları](#model-notlari)).

## Çalıştırma
Sohbeti başlatmak için:
```powershell
python -m assistant.cli chat --config .\config\settings.yaml
```

Yerel notları hafızaya almak için (varsayılan allowlist: `notes/`):
```powershell
# Opsiyon 1 (flag):
python -m assistant.cli ingest-notes --path .\notes
# Opsiyon 2 (pozisyonel):
python -m assistant.cli ingest-notes .\notes
```

`ingest-notes` neden var? Not klasöründeki `.txt/.md` içerikleri semantik hafızaya ekler; böylece sohbet sırasında ilgili not parçaları bağlam olarak geri çağrılabilir.

Profil özetini görmek için:
```powershell
python -m assistant.cli profile
```

### Hafıza Katmanları (agentik yapı)
- **Working Memory**: Son birkaç mesajlık kısa bağlam (ayar: `working.window`).
- **Episodic Memory**: Geçmiş sohbet turları, zaman ve kaynakla kayıtlı.
- **Semantic Memory**: Not ingest (`ingest-notes`) ile eklenen bilgi parçaları.
- **Temporal Truth**: Zamanla güncellenen gerçekler; yeniler eskilere göre daha yüksek güvenle tutulur.
- **Procedural Memory**: Etkileşim kuralları ve beceriler (ayar: `procedural.rules`).

## Konfigürasyon
- `config/settings.yaml`: Ortam, model ve hafıza ayarları.
- `config/allowlist.yaml`: Güvenli komut/klasör listesi.
- `.env` (opsiyonel): API anahtarları gerekmez; sadece özel yol/port gibi ayarlar için kullanılabilir.

## Dosya Ağacı
```
README.md
requirements.txt
pyproject.toml
config/
  settings.yaml
  allowlist.yaml
assistant/
  __init__.py
  cli.py
  config/
    __init__.py
    loader.py
    schemas.py
  llm/
    __init__.py
    clients.py
    prompts.py
  memory/
    __init__.py
    embedding.py
    store.py
    temporal.py
  services/
    __init__.py
    conversation.py
    profiling.py
  tools/
    __init__.py
    notes.py
    commands.py
  logging_config.py
  typing.py
  utils.py
docs/
  PLAN.md
  CHECKLIST.md
tests/
  __init__.py
  test_config.py
  test_memory.py
  test_conversation.py
```

## Testler
```powershell
python -m pytest
```

## Model Notları
- **Sohbet**: `aya-expanse:8b` (Ollama), iyi Türkçe; alternatif: `mistral-small:latest`. VRAM: ~12-16GB (4070 Ti yeterli).
- **Embedding**: `intfloat/multilingual-e5-large` (SentenceTransformers). VRAM ~2-4GB, CPU ile de çalışır.
- **Özetleme**: Aynı sohbet modeli kullanılabilir; gerekirse daha hafif `mistral:7b`.

Offline senaryo için modelleri USB ile `C:\Users\Mustafa\.ollama\models` veya LM Studio'nun model klasörüne kopyalayın.

## Fotoğraf Pipeline Taslağı
- **Girdi**: `photos/inbox/` dizinine manuel eklenen fotoğraflar.
- **Ön işleme**: `python -m assistant.cli ingest-notes --path photos/inbox` (metin açıklamaları olan .txt/.md eşlik dosyaları).
- **Görsel model (gelecek)**: Lokal `BLIP` veya `LLaVA` türevleri; GPU VRAM kontrolü ile çalıştır.
- **Güvenlik**: Ham görseller `photos/raw/` altında tutulur; özetler `data/summaries/` içinde şifreli disk üzerinde saklanır (BitLocker önerilir).
