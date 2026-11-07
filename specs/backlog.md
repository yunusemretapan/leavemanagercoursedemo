# Backlog — deferred findings

Findings a human triaged as **defer**: real, but fixed later by decision (`workflows/feature-development.md`,
step 7). Nothing lands here without that decision; noise is rejected in the triage record, not parked here.

- A criterion moved out at the ship gate (R-08, `→ moved to B-<n>`) lands here too, by the
  human's ship decision; the entry names the spec and criterion.
- One entry per finding, newest last. Delete the entry in the commit of the work that closes it.
- An entry that grows into new behavior becomes a spec (`specs/active/`), not a fix.

<!-- Format (labels stay English):
- **B-<n>** — <finding, one line> — Source: spec <NNNN>, review round <n> (<file:line>) — Severity: <…>
  — Recommendation: <the reviewer's action> — Deferred by: <name>, <YYYY-MM-DD>, <why>
  A decision deferred at bootstrap (its REPORT) uses Source: bootstrap <YYYY-MM-DD>.
-->

- **B-2** — `StarletteDeprecationWarning`: `starlette.testclient` ile `httpx` kullanımı deprecated (`httpx2` öneriliyor); şimdilik zararsız uyarı — Source: spec 0001, VERIFY round 2 — Severity: Info — Recommendation: bir sonraki bağımlılık güncellemesinde TestClient taşıması, lock yenilenerek — Deferred by: yunusemretapan, 2026-11-07, SHIP'i engellemiyor
- **B-3** — `503` güvenlik ağı (`_is_contention`) mesaj metniyle eşleşiyor ve log yazmıyor: gerçek çekişme (`SQLITE_BUSY`) ile programlama hatası türü `SQLITE_LOCKED` ayrılmıyor, kalıcı çekişme operatöre görünmüyor — Source: spec 0003, review round 3 (`app/data/database.py:11-15`, `:61-63`) — Severity: Low — Recommendation: `exc.sqlite_errorcode & 0xFF == sqlite3.SQLITE_BUSY` ile hata kodu bazlı eşleşme, `503`'e çevirmeden önce `WARNING` log; "database table is locked" için maskelememe testi — Deferred by: yunusemretapan, 2026-11-07, bugün tetiklenmiyor; kriter/güvenlik/veri etkisi yok
- **B-4** — Kimliği doğrulanmamış `429` seli oturumlu istekleri tek SQLite yazıcısının sırasına sokuyor (ölçüm: ~13× yavaşlama, hata yok; daha büyük selde busy timeout sonrası `503`) — Source: spec 0003, review round 3 (`app/business/login_throttle.py:55-57`, `app/business/auth.py:86`) — Severity: Info — Recommendation: CHANGE talebi: kilit ve IP sınırı önce deferred okumayla denetlensin, `IMMEDIATE` + purge yalnızca kabul edilen denemede; R-6 ("her giriş denemesinde temizlenir") gevşetilmeli, R-1a yeniden kanıtlanmalı — Deferred by: yunusemretapan, 2026-11-07, kurs demosu; hiçbir AC işlem hızı vaat etmiyor
- **B-5** — Hata sonrası parolanın temizlenmesi (`web/js/main.js`, `passwordInput.value = ''`) hiçbir otomatik testle sabitlenmiyor: satır silinince web testleri yeşil kalıyor (spec 0002'den, DOM katmanı test dışında) — Source: spec 0003, VERIFY (F-A) — Severity: Low — Recommendation: parola temizleme kararını saf bir görünüm fonksiyonuna taşı (ör. `clearPassword: true`) ve `node --test` ile sabitle — Deferred by: yunusemretapan, 2026-11-07, bu spec'te değişmeyen kod; ekran görüntüsü ve DOM gözlemiyle kanıtlı
