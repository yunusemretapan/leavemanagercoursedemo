# Architecture

> Bootstrap 2026-11-07'de dolduruldu. Karar verilmiş mimari; ajanlar planlamadan önce okur.

## System overview

Leave Manager tek süreçli, tek repolu bir **n-katmanlı (3 katman + ortak modeller)** web
uygulamasıdır. Python 3.13 + FastAPI bir REST API (`/api/*`) sunar ve aynı süreçte
`web/` altındaki düz HTML/CSS/JS dosyalarını `StaticFiles` ile servis eder (tek origin, CORS yok).
Veri, standart kütüphane `sqlite3` ile tek bir SQLite dosyasında tutulur; ORM yoktur.
Neden: klasik n-katman kurs katılımcıları için tanıdıktır, iş kuralları veritabanından bağımsız
unit test edilebilir kalır ve bu ölçek için modüler monolit/mikroservis gereğinden ağırdır.

```
app/
  api/            # Sunum: FastAPI router'ları, Pydantic şemaları, oturum, HTTP hata eşlemesi
  business/       # İş: kullanım senaryoları + iş kuralları (saf fonksiyonlar), yetki, transaction sınırı
  data/           # Veri erişimi: sqlite3 repository'leri, SQL yalnızca burada; migrations/NNNN_*.sql
  models/         # Saf dataclass/enum'lar, DomainError hiyerarşisi, Clock arayüzü
  main.py         # Uygulama kurulumu, bağımlılık bağlama, StaticFiles, lifespan (migration)
web/              # index.html, css/, js/ (ES modules), tests/ (node --test)
tests/            # unit/ (business) · integration/ (api + geçici SQLite)
```

## Modules / components and ownership

| Module | Single responsibility | Owns |
|---|---|---|
| `app/api` | HTTP sınırı: istek doğrulama (Pydantic), oturumdan kullanıcıyı çözme, `DomainError` → HTTP eşlemesi | İstek/yanıt şemaları, hata gövdesi biçimi |
| `app/business` | Kullanım senaryoları (talep oluştur, onayla, reddet, iptal, listele, bakiye) ve iş kuralları BR-1…BR-8, yetkilendirme | İş kuralları, durum geçişleri, transaction sınırı |
| `app/data` | Kalıcılık: repository'ler, parametreli SQL, bağlantı yönetimi, migration'lar, seed | SQLite şeması ve verisi |
| `app/models` | Katmanlar arası taşınan saf tipler | `Employee`, `LeaveRequest`, `RequestStatus`, `LeaveType`, `DomainError`'lar, `Clock` |
| `app/main.py` | Bileşim kökü: katmanları birbirine bağlar | Uygulama yapılandırması |
| `web/` | Kullanıcı arayüzü; saf görünüm fonksiyonları + ince DOM bağlama katmanı | Ekran durumları |

## Communication rules

- Çağrı yönü yalnızca aşağı doğrudur: `api → business → data`; her katman `models`'i kullanabilir.
- Katmanlar arası doğrudan fonksiyon çağrısı; event/mesaj kuyruğu yok.
- `business` repository'lere `main.py`/`api` bağımlılık enjeksiyonu (FastAPI `Depends`) ile verilen nesneler üzerinden erişir; transaction'ı `business` başlatır ve bitirir.
- `web/` backend ile yalnızca `/api/*` JSON uç noktaları üzerinden konuşur.

## Forbidden dependencies (make them testable)

Hepsi `import-linter` sözleşmeleri olarak `pyproject.toml` içinde tanımlanır ve `scripts/check`
içindeki `architecture` adımında denetlenir.

1. **Katman atlama yok:** `app.api` → `app.data` ve `app.api` → `sqlite3` import'u yasak (her zaman `app.business` üzerinden).
2. **Yukarı import yok** (`layers` sözleşmesi `api > business > data`): `app.data` → `app.business`/`app.api` ve `app.business` → `app.api` yasak.
3. `app.business` → `fastapi`, `starlette` yasak (iş katmanı HTTP'den habersiz).
4. `app.models` → `app.api`, `app.business`, `app.data`, `fastapi`, `starlette`, `pydantic`, `sqlite3` yasak (yalnızca standart kütüphane).
5. `web/` backend koduna bağlanmaz; tek arayüzü `/api/*` (kod yapısı gereği; review'da denetlenir).

Üçüncü taraf kütüphane politikası: `docs/security.md` "Dependencies".

## Deliberately out of scope

- Gerçek kimlik doğrulama (parola, SSO) — demo oturumu kullanılır (`docs/security.md`).
- İK/Admin rolü, organizasyon ağacı, çok seviyeli onay.
- Yıllık izin dışındaki izin türleri, yarım gün izin, resmî tatil takvimi, kıdeme göre hak ediş, devreden bakiye.
- Onaylanmış iznin iptali.
- Bildirim (e-posta vb.), raporlama, çoklu dil.
- Frontend build adımı, frontend framework'ü, tarayıcı e2e testleri.
- Üretim dağıtımı, Docker.
