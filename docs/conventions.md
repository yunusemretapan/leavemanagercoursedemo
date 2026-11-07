# Conventions

> Bootstrap 2026-11-07'de dolduruldu. Yalnızca gerçek kurallar: her kural ya araçla zorlanır
> (tercih edilen) ya da review'da denetlenir. Temenniler buraya girmez.

## Language
<!-- Set at bootstrap (step 0) and mirrored in AGENTS.md. Changing it later is allowed — edit both
     places; existing documents are not translated retroactively. -->
- Chat language (interviews, sessions): Türkçe (`tr`)
- Document language (docs/, specs, plans, ADRs, review and verify reports): Türkçe (`tr`)
- Always English (protocol, not prose): ANEW core files, template headings and field labels,
  `Status:` values (Draft / Approved / In progress / Shipped), `Approved by / on:`, `Source:`.
- Code identifiers, branch names, commit messages: İngilizce. Kullanıcıya görünen arayüz metinleri
  ve API hata `message` alanı: Türkçe.
- Agent messages (handoff summaries, refusals, `Next:` lines): chat language; command names, file
  paths and protocol fields verbatim.

## Language & framework versions
- **Python 3.13** — `.python-version` ve `pyproject.toml` `requires-python = ">=3.13,<3.14"` ile sabit.
- Sanal ortam: `.venv` (`py -3.13 -m venv .venv`), paketler `pip` ile; venv yorumlayıcısı her yerde
  `./scripts/py` ile çağrılır (Windows ve Linux'ta aynı komut, check.conf da bunu kullanır); bağımlılıklar `pyproject.toml`'da,
  kesin sürümler `requirements.lock` (pip-tools `pip-compile`) ile kilitli.
- FastAPI + Uvicorn + Pydantic v2; veritabanı standart kütüphane `sqlite3` (ORM yok).
- Geliştirme araçları: pytest, Ruff (lint + format), mypy (strict), import-linter, pip-audit, pip-tools.
- Frontend: düz HTML/CSS/JS (ES modules), build adımı yok; testler Node'un yerleşik `node --test`'i
  (Node 20+; bu makinede Node 26). npm bağımlılığı yok.
- Kesin paket sürümleri walking skeleton'da güncel kararlı sürümlerle kilitlenir.

## Naming
- Python: modül/fonksiyon/değişken `snake_case`, sınıf `PascalCase`, sabit `UPPER_SNAKE_CASE`.
- JS: değişken/fonksiyon `camelCase`, dosya `kebab-case.js`.
- Testler: `tests/unit/test_<modül>.py`, `tests/integration/test_<uç nokta>.py`, `web/tests/<modül>.test.js`.
  Test adı davranışı anlatır: `test_request_exceeding_balance_is_rejected`.
- Integration testleri `@pytest.mark.integration` taşır (fast/full ayrımının seçicisi).
- API yolları: `/api/<çoğul-isim>` (ör. `/api/leave-requests`, `/api/leave-requests/{id}/approve`).
- Migration dosyaları: `app/data/migrations/NNNN_<kısa_ad>.sql`, sıralı, uygulanmış olan asla değiştirilmez.
- Branch ve commit adları: `docs/git.md`.

## Error handling
- `business` katmanı iş kuralı ihlalinde `app/models` içindeki `DomainError` alt sınıflarını fırlatır
  (ör. `InsufficientBalance`, `OverlappingRequest`, `InvalidDateRange`, `NotAuthorized`, `NotFound`,
  `InvalidStateTransition`). Her alt sınıf sabit bir İngilizce `code` ve Türkçe `message` taşır.
- `api` katmanında **tek** bir exception handler eşler: Pydantic doğrulama → `422`, oturum yok / süresi doldu / hatalı giriş
  (`Unauthenticated`, `SessionExpired`, `InvalidCredentials`) → `401`,
  `NotAuthorized` → `403`, `NotFound` → `404`, `ServiceUnavailable` (veri deposuna erişilemiyor) → `503`,
  diğer kural ihlalleri → `409`. Eşleme tablosu: `app/api/errors.py` (`STATUS_BY_ERROR`).
- Yanıt gövdesi her zaman: `{"error": {"code": "<EN_CODE>", "message": "<Türkçe mesaj>"}}`.
- Router'larda `try/except` ile hata yutmak veya `HTTPException`'ı iş kuralı için kullanmak yasak.
- Kullanıcıya **asla** sızmayanlar: stack trace, SQL, dosya yolları, iç exception mesajları.
  Beklenmeyen hata → `500` + genel mesaj; ayrıntı sunucu log'una.

## Data rules
- İzin tarihleri saatsiz `datetime.date`; API'de ISO-8601 `YYYY-MM-DD`; SQLite'ta `TEXT` (ISO).
- Zaman damgaları (`created_at`, `decided_at`) UTC, ISO-8601 `Z` sonekli `TEXT`.
- "Bugün" ve "şimdi" yalnızca enjekte edilen `Clock`'tan gelir; `date.today()`, `datetime.now()`,
  `datetime.utcnow()` doğrudan kullanılmaz. Arayüz `app/models/clock.py` (`Clock`, `SystemClock`);
  testte `tests/conftest.py` `FakeClock`.
- Gün sayıları `int` (yarım gün yok). Kimlikler SQLite `INTEGER PRIMARY KEY`.
- Durum ve tür alanları `Enum` (İngilizce değerler: `PENDING / APPROVED / REJECTED / CANCELLED`, `ANNUAL`);
  DB'de enum değeri `TEXT` olarak, `CHECK` kısıtıyla.
- SQL yalnızca parametreli (`?`), string birleştirme/f-string ile SQL yasak.
- Şema yalnızca migration dosyalarıyla değişir; uygulama açılışında (lifespan) sırayla uygulanır.

## Known traps
<!-- Format: "<trap> — <what to do instead> — from <spec/finding>". Builders read this section
     before the first plan step. A trap that tooling can catch moves to "Enforced by tooling". -->
- Naif `datetime.now()`/`date.today()` — enjekte edilen `Clock` (UTC) kullan — from bootstrap 2026-11-07
- `sqlite3` bağlantısını thread'ler arasında paylaşmak — her istek kendi bağlantısını açar/kapatır, açılışta `PRAGMA foreign_keys=ON` — from bootstrap 2026-11-07
- Makinedeki Python 3.7 ile çalışmak (çıplak `python`/`pip`) — her zaman `.venv` yorumlayıcısı (`.venv/Scripts/python -m …` Windows, `.venv/bin/python -m …` Linux) — from bootstrap 2026-11-07
- `TestClient(app)`'i `with` olmadan kurmak (lifespan/migration çalışmaz) — istemciyi her zaman bir fixture içinde `with TestClient(app) as client:` ile kur — from bootstrap 2026-11-07
- Windows'ta `mimetypes` kayıt defterinden `.js` → `text/plain` okur, tarayıcı ES module script'i reddeder ve sayfa çalışmaz — composition root'ta `mimetypes.add_type("text/javascript", ".js")` (sonrasında `mimetypes.init()` çağrılmaz, eşlemeyi geri alır) (`app/main.py`); testi `test_module_scripts_are_served_as_javascript_even_if_os_says_text_plain` — from spec 0001 VERIFY F-V1
- Starlette `.env` okuyucusu (`starlette.config.Config`) değerleri kırpar ve çevreleyen tırnakları atar; ortam değişkeni kırpılmaz — boşluk/tırnak taşıyabilen sırları ortam değişkeniyle verin, `.env` davranışını `.env.example`/README'de belgeleyin — from spec 0002 review F-3
- FastAPI'nin `strict_content_type` varsayılanını (True) kapatmak — Content-Type'sız JSON gövdeleri kabul edilir ve R-11'in JSON-only CSRF katmanı kaybolur; kapatılmaz (testler: `test_non_json_logout_is_rejected_and_session_survives`, `test_json_login_without_content_type_is_rejected`) — from spec 0002 review round 2 F-2
- Pydantic `date` alanının saat içeren değerleri gevşekçe kabul etmesi — tarih alanlarında strict mod + `YYYY-MM-DD` doğrulaması — from bootstrap 2026-11-07

## Enforced by tooling
<!-- What the compiler/linter/analyzers already enforce, so review doesn't re-litigate it. -->
- **Ruff lint** (`ruff check`): `E, F, I, B, UP, S, ASYNC, PTH, DTZ` kural setleri — `S608` (string ile SQL),
  `ASYNC` (`async def` içinde bloklayan çağrı; route'lar düz `def`), `PTH` (string yol birleştirme yerine
  `pathlib`), `DTZ` (naif datetime).
- **Ruff format** (`ruff format --check`): tek biçim, tartışma yok.
- **mypy --strict**: tip hataları.
- **import-linter**: `docs/architecture.md` "Forbidden dependencies" 1–4.
- **pytest `--strict-markers`**: kayıtsız/yanlış yazılmış marker hata verir (fast/full ayrımı sessizce kaymaz).
- **`.gitattributes`**: LF satır sonu (Windows CRLF tuzağı).
