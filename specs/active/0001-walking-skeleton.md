# Spec 0001 — walking skeleton

- Status: In progress
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

- [ ] AC-1 — `README.md` "Çalıştırma" bölümünde belgelenen başlatma komutu çalıştırıldığında, 10 saniye içinde `127.0.0.1:8000` adresindeki sağlık kontrolü başarı döner; adres/port ortam değişkeniyle değiştirildiğinde aynısı verilen adreste olur.
- [ ] AC-2 — Kök adres, `lang="tr"`, tek `h1` "Leave Manager" ve `aria-live="polite"` durum bölgesi içeren başlangıç sayfasını döner.
- [ ] AC-3 — Sağlık kontrolü, uygulama ve veri deposu erişilebilirken başarı yanıtı döner; veri deposuna erişilemiyorsa "hizmet kullanılamıyor" (503) ve standart hata gövdesi döner.
- [ ] AC-4 — Veri deposu yokken ilk açılış onu oluşturur ve tüm şema sürümlerini uygular; ikinci açılış hiçbir sürümü tekrar uygulamaz ve mevcut veriyi korur.
- [ ] AC-5 — Bilinmeyen bir API yolu 404 ve standart hata gövdesi döner; beklenmeyen bir hata 500, genel bir Türkçe mesaj ve standart gövde döner, yanıtta stack trace/dosya yolu yoktur.
- [ ] AC-6 — Başlangıç sayfasının durum görünümü üç durumu doğru metinle üretir: yükleniyor, başarı, hata.
- [ ] AC-7 — `./scripts/check` sekiz planlanan adımı koşar ve yeşildir; `./scripts/check --fast` yalnızca altı `[fast]` adımı koşar ve yeşildir; unit, integration ve web katmanının her birinde en az bir test koşar.
- [ ] AC-8 — `docs/architecture.md` "Forbidden dependencies" 1–4'ten herhangi birini ihlal eden bir import, `architecture` adımını kırmızıya çevirir.
- [ ] AC-9 — CI, push'ta Python 3.13 ve Node kurup full `./scripts/check`'i koşar ve yeşildir (kanıt: HEAD SHA'sına ait CI run bağlantısı).

## Definition of Done
- [ ] Every acceptance criterion mapped to proof (test or reproducible observation)
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [ ] Docs / ADRs updated if behavior or architecture changed (`README.md` "Çalıştırma" bölümü dahil)
- [ ] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | |
| Fix rounds | |
| Review findings: real / noise / deferred | |
| Regressions introduced | |
| Bugs escaped to production | |
