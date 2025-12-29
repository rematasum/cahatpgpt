# Faz Checklistleri

## Faz 0
- [ ] `python -m assistant.cli chat` çalışıyor (stub LLM kabul).
- [ ] `data/memory.sqlite` oluştu ve mesajlar kaydedildi.
- [ ] `config/settings.yaml` okunuyor, loglar `logs/` altına yazılıyor.
- [ ] Pytest temel testleri geçiyor.

## Faz 1
- [ ] Ollama/LM Studio modeli çağrılıyor, Türkçe çıktı veriyor.
- [ ] Embedding modeli lokal yüklendi, anı aramaları çalışıyor.
- [ ] Episodic/semantic kayıtlar timestamp, kaynak, güven skoru ile kaydediliyor.
- [ ] `ingest-notes` komutu allowlist içindeki dosyaları hafızaya ekliyor.
- [ ] Profil çıkarımı `profile` komutuyla okunabiliyor.
- [ ] Komut çalıştırma sadece `config/allowlist.yaml` izin verdiği komutları kullanıyor.

## Faz 1.5
- [ ] Günlük/haftalık özetleme çıktıları `data/summaries/` içine yazılıyor.
- [ ] Decay/forget heuristiği çalışıyor (skor güncelleniyor).
- [ ] Temporal truth sürümleme tabloları güncel.
- [ ] Kaynak takibi raporu alınabiliyor (`profile --report`).
- [ ] Yansıma mesajı düzenli olarak LLM sistem promptunda.

## Faz 2 (Tasarım)
- [ ] STT/TTS bileşenleri için modül taslakları yazıldı.
- [ ] Wake-word kontrolü tanımlandı, yanlış pozitif stratejisi belgelendi.
- [ ] Mikrofon verisi şifreleme ve retention politikası dökümante edildi.
- [ ] Kullanıcı kontrolü: açık/kapalı komutu, ışık/ikon göstergesi tasarlandı.
