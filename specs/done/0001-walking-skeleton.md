# Spec 0001 — walking skeleton

- Status: Shipped
- Mode: lite
- Plan: `specs/plans/0001-plan.md`
- Self-critique: done

## Intent

Geliştirici (ve kurs katılımcıları), henüz hiçbir iş özelliği yokken uygulamanın uçtan uca
çalıştığını ve doğrulama sözleşmesinin (`scripts/check`) gerçekten bir şey kanıtladığını görmek
istiyor. Başarı: tek bir komutla uygulama açılır, tarayıcıda Türkçe bir başlangıç sayfası sistemin
durumunu gösterir, veri deposu ilk açılışta kendiliğinden hazırlanır ve `scripts/check` bootstrap'ta
planlanan tüm adımları bu makinede ve CI'da yeşil koşar. Bilinçli olarak yapılmayan: hiçbir izin
özelliği (talep, bakiye, onay), giriş/oturum ve demo kullanıcılar — bunlar sonraki spec'lerdir.

## Requirements

- R-1: Uygulama yerelde, belgelenmiş tek bir komutla başlatılabilir; varsayılan olarak yalnızca bu
  makineden (`127.0.0.1`, port `8000`) erişilir; adres ve port ortam değişkeniyle değiştirilebilir.
- R-2: Uygulamanın kök adresi, Türkçe başlıklı bir başlangıç sayfası sunar; sayfa, sistemin
  durumunu uygulamadan sorgulayıp kullanıcıya gösterir.
- R-3: Uygulama, kendisinin ve veri deposunun erişilebilir olduğunu bildiren bir sağlık kontrolü
  sunar. Veri deposuna erişilemiyorsa sağlık kontrolü "hizmet kullanılamıyor" anlamında bir hata
  döner.
- R-4: Uygulama ilk açılışta veri deposu yoksa onu oluşturur ve şema sürümlerini uygular. Var olan
  bir veri deposuyla yeniden açıldığında uygulanmış sürümleri tekrar uygulamaz ve veriyi korur.
  Veri deposunun konumu varsayılan olarak repodaki, git'e girmeyen bir veri klasörüdür; ortam
  değişkeniyle değiştirilebilir.
- R-5: Bilinmeyen bir API yolu ve her beklenmeyen hata, proje standardı hata gövdesiyle
  (`docs/conventions.md` "Error handling") döner; iç ayrıntı (stack trace, dosya yolu, SQL) sızmaz.
- R-6: `scripts/check` bootstrap'ta planlanan adımları (lint, format, types, architecture, unit,
  web-test, integration, audit) gerçek komutlarla koşar; `--fast` yalnızca `[fast]` etiketli
  olanları koşar. Her test katmanında (unit, integration, web) en az bir gerçek test vardır.
- R-7: Katman sınırları (`docs/architecture.md` "Forbidden dependencies" 1–4) araçla zorlanır:
  yasak bir import `scripts/check`'i kırmızıya çevirir.
- R-8: CI, her push'ta full profili Python 3.13 ve Node ile koşar.
- R-9: `README.md`, Türkçe bir "Çalıştırma" bölümüyle ortamın kurulmasını, başlatma komutunu ve
  ortam değişkenlerini anlatır.

## User experience

- Flow: Kullanıcı tarayıcıda uygulamanın kök adresini açar → "Leave Manager" başlıklı sayfa
  yüklenir → sayfa sistem durumunu kontrol eder ve sonucu gösterir.
- States:
  - **Yükleniyor:** "Sistem durumu kontrol ediliyor…"
  - **Başarı:** "Sistem çalışıyor" (uygulama ve veri deposu erişilebilir).
  - **Hata:** "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin." (sağlık kontrolü başarısız
    veya yanıt yok).
  - Boş durum ve yetki yok durumu: uygulanamaz (veri ve giriş yok).
- Design reference: none — the flow above is the design.
- Accessibility: sayfa dili `tr`; tek bir ana başlık (`h1`); durum metni ekran okuyucuya duyurulan
  bir canlı bölgede (`aria-live="polite"`); durum yalnızca renkle değil metinle iletilir.

## Constraints & out of scope

- Sensitive area: none.
- Ortam: Python 3.13 (bootstrap'ta kuruldu), Node 20+ (bu makinede 26). Profil kararı PLAN
  kapısında doctor'ın per-profile çıktısıyla (R-13).
- `audit` adımı ağ gerektirir (yalnızca full; `requires` satırlı).
- Beklenmeyen hata davranışı (AC-5) yalnızca testte kaydedilen bir hata yoluyla kanıtlanır; üretim
  koduna hata fırlatan yol eklenmez.
- Sağlık kontrolü yanıtının biçimi planda belirlenir; spec yalnızca "uygulama ve veri deposu
  erişilebilir" bilgisini ister.
- Out of scope: izin talebi, bakiye, onay/red; giriş, oturum ve `SESSION_SECRET` zorunluluğu
  (giriş spec'i ile gelir); seed/demo kullanıcılar; iş tabloları (yalnızca şema sürüm kaydı);
  üretim dağıtımı; frontend build adımı; e2e testleri.

## Acceptance criteria

- [x] AC-1 — `README.md` "Çalıştırma" bölümünde belgelenen başlatma komutu çalıştırıldığında, 10 saniye içinde `127.0.0.1:8000` adresindeki sağlık kontrolü başarı döner; adres/port ortam değişkeniyle değiştirildiğinde aynısı verilen adreste olur.
- [x] AC-2 — Kök adres, `lang="tr"`, tek `h1` "Leave Manager" ve `aria-live="polite"` durum bölgesi içeren başlangıç sayfasını döner.
- [x] AC-3 — Sağlık kontrolü, uygulama ve veri deposu erişilebilirken başarı yanıtı döner; veri deposuna erişilemiyorsa "hizmet kullanılamıyor" (503) ve standart hata gövdesi döner.
- [x] AC-4 — Veri deposu yokken ilk açılış onu oluşturur ve tüm şema sürümlerini uygular; ikinci açılış hiçbir sürümü tekrar uygulamaz ve mevcut veriyi korur.
- [x] AC-5 — Bilinmeyen bir API yolu 404 ve standart hata gövdesi döner; beklenmeyen bir hata 500, genel bir Türkçe mesaj ve standart gövde döner, yanıtta stack trace/dosya yolu yoktur.
- [x] AC-6 — Başlangıç sayfasının durum görünümü üç durumu doğru metinle üretir: yükleniyor, başarı, hata.
- [x] AC-7 — `./scripts/check` sekiz planlanan adımı koşar ve yeşildir; `./scripts/check --fast` yalnızca altı `[fast]` adımı koşar ve yeşildir; unit, integration ve web katmanının her birinde en az bir test koşar.
- [x] AC-8 — `docs/architecture.md` "Forbidden dependencies" 1–4'ten herhangi birini ihlal eden bir import, `architecture` adımını kırmızıya çevirir.
- [x] AC-9 — CI, push'ta Python 3.13 ve Node kurup full `./scripts/check`'i koşar ve yeşildir (kanıt: HEAD SHA'sına ait CI run bağlantısı).

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation)
- [x] `scripts/check` green
- [x] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [x] Docs / ADRs updated if behavior or architecture changed (`README.md` "Çalıştırma" bölümü dahil)
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Evidence (VERIFY round 2, HEAD 772f56c)
Full green: CHECK GREEN (full, 8 steps, 8 s) @1de7bf0 — https://github.com/yunusemretapan/leavemanagercoursedemo/actions/runs/42374854426 ·
HEAD @772f56c — https://github.com/yunusemretapan/leavemanagercoursedemo/actions/runs/42374989836 (fark yalnızca `specs/`).
Yeniden üretim: `./scripts/check`. Kasıtlı bozmalar repo dışındaki geçici kopyalarda, QA tarafından.

| Acceptance criterion | Evidence | Status |
|---|---|---|
| AC-1 | `test_app_starts_and_answers_health_on_configured_port` (`LEAVE_HOST=127.0.0.2`), `test_settings_default_to_localhost_8000`; canlı: varsayılan `127.0.0.1:8000` sağlık 200 (~2 s); bozma: sabit port → kırmızı | PASS |
| AC-2 | `test_index_page_has_lang_heading_and_live_region`; S-1…S-3b | PASS |
| AC-3 | `test_health_ok_when_database_reachable`, `test_health_503_when_database_unreachable`, `test_check_health_raises_when_database_down`; bozma: ping hatası yutulunca → kırmızı; canlı 503 | PASS |
| AC-4 | `test_first_start_applies_all_migrations`, `test_second_start_reapplies_nothing_and_keeps_data`; bozmalar: atlama kaldırıldı / DB silindi → kırmızı | PASS |
| AC-5 | `test_unknown_api_path_returns_standard_404`, `test_unexpected_error_returns_generic_500_without_internals`; bozmalar: `repr(exc)` sızıntısı / handler kaydı yok → kırmızı | PASS |
| AC-6 | `web/tests/status-view.test.js` (5), `test_module_scripts_are_served_as_javascript_even_if_os_says_text_plain`; Windows gerçek tarayıcı S-1…S-3b; bozmalar: `add_type` / `httpOk` kaldırıldı → kırmızı | PASS |
| AC-7 | full 8 adım, fast 6 adım; unit 6, integration 9, web 5 | PASS |
| AC-8 | Dört sözleşmenin her biri kasıtlı ihlalle BROKEN, `architecture` rc=1 (QA, VERIFY round 1) | PASS |
| AC-9 | CI run 42374989836 @772f56c (setup-python 3.13, setup-node 26, full check) | PASS |

UI: S-1 yükleniyor · S-2 başarı · S-3a hata (503) · S-3b hata (yanıt yok) — S-1…S-3b agent-captured, judged by yunusemretapan at SHIP, 2026-11-07.

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 0 |
| Fix rounds | 3 |
| Review findings: real / noise / deferred | 5 / 2 / 1 (B-2) |
| Regressions introduced | 0 |
| Bugs escaped to production | 0 (üretime çıkmıyor) |
