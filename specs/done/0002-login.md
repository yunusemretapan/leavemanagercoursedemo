# Spec 0002 — kullanıcılar, parolalı giriş ve oturum

- Status: Shipped
- Mode: lite
- Plan: `specs/plans/0002-plan.md`
- Self-critique: done

## Intent

İzin akışının "kim istiyor, kim onaylıyor" sorusunu yanıtlayabilmesi için uygulamanın kullanıcıyı
güvenilir biçimde tanıması gerekiyor. Kullanıcı, kullanıcı adı ve parolasıyla giriş yapar;
uygulama oturum boyunca onun kim olduğunu ve rolünü (Çalışan / Yönetici) bilir; girişsiz hiçbir
kişisel veri alınamaz. Başarı: kurs katılımcısı altı demo kullanıcıdan biriyle giriş yapıp
çıkabilir, parolalar ve oturumlar güvenlik pratiklerine uygun yönetilir ve sonraki spec'ler
(bakiye, talep, onay) "isteği yapan kim?" sorusuna güvenilir bir yanıt bulur. Bilinçli olarak
yapılmayan: kaba kuvvet (brute force) koruması (spec 0003), parola değiştirme/sıfırlama, kullanıcı
yönetimi ve izin özellikleri.

## Requirements

- R-1: İlk açılışta altı kurgusal demo kullanıcı vardır (aşağıdaki tablo); yeniden açılışta
  çoğaltılmaz. Hepsinin başlangıç parolası, repoya girmeyen `DEMO_PASSWORD` yapılandırma
  değerinden gelir (ortam değişkeni, yoksa repo kökündeki `.env`).

  | Kullanıcı adı | Ad | Rol | Yöneticisi |
  |---|---|---|---|
  | `ayse.yilmaz` | Ayşe Yılmaz | Yönetici | — (üst yönetici) |
  | `mehmet.kaya` | Mehmet Kaya | Yönetici | Ayşe Yılmaz |
  | `ali.demir` | Ali Demir | Çalışan | Ayşe Yılmaz |
  | `zeynep.sahin` | Zeynep Şahin | Çalışan | Ayşe Yılmaz |
  | `can.ozturk` | Can Öztürk | Çalışan | Mehmet Kaya |
  | `elif.arslan` | Elif Arslan | Çalışan | Mehmet Kaya |

- R-2: **Parola politikası** — bir parola en az 12, en fazla 128 karakterdir; kullanıcı adına
  eşit olamaz (büyük/küçük harf duyarsız); yaygın parolalar listesindekiler kabul edilmez.
  Karakter sınıfı zorunluluğu yoktur. Yaygın parolalar listesi repoda sabittir, en az 100 giriş
  içerir (uluslararası en yaygınlar ve Türkçe karşılıkları) ve büyük/küçük harf duyarsız
  karşılaştırılır. Uzunluk Unicode karakter sayısıyla ölçülür; parola kırpılmaz. Politika, bir parolanın belirlendiği her noktada uygulanır
  (bu spec'te: demo parolası).
- R-3: `DEMO_PASSWORD` yoksa veya politikaya uymuyorsa uygulama açılmayı reddeder ve nedeni
  (parolanın kendisini yazmadan) Türkçe açıkça bildirir.
- R-4: Parolalar asla düz metin saklanmaz; kullanıcıya özgü rastgele tuzla (salt), yavaş bir
  parola türetme fonksiyonuyla saklanır. Doğrulama sabit zamanlı karşılaştırma ile yapılır.
- R-5: Kullanıcı, kullanıcı adı (baştaki/sondaki boşluk kırpılır, büyük/küçük harf duyarsız) ve
  parolayla giriş yapar. Başarılı
  girişte yeni bir oturum açılır ve kullanıcının adı ve rolü döner.
- R-6: Başarısız girişte (yanlış parola veya olmayan kullanıcı) yanıt tektir ve geneldir:
  "Kullanıcı adı veya parola hatalı." Olmayan kullanıcıda da parola doğrulaması yapılır; yanıt,
  hesabın var olup olmadığını ele vermez. Kullanıcı listesi hiçbir yerde açıkça sunulmaz.
- R-7: Oturum sunucu tarafında tutulur: tarayıcıda yalnızca rastgele bir oturum belirteci
  bulunur, sunucu belirtecin yalnızca özetini (hash) saklar. Belirteç çerezi `HttpOnly` ve
  `SameSite=Lax`'tır; `Secure` bayrağı yapılandırmayla açılır. Her başarılı girişte yeni bir
  belirteç üretilir.
- R-8: Oturum, açılışından **8 saat** sonra (mutlak) veya **30 dakika** hareketsizlikten sonra
  sona erer. Süre, uygulamanın saatinden (`Clock`) ölçülür. Süresi dolmuş bilinen bir belirteç
  `401` ve `SESSION_EXPIRED` kodunu, belirteç yok veya geçersizse `401` ve `UNAUTHENTICATED`
  kodunu alır. Süresi dolmuş oturum fark edildiğinde silinir; her başarılı girişte süresi dolmuş
  tüm oturumlar temizlenir.
- R-9: Çıkış, oturumu sunucuda hemen geçersiz kılar; eski belirteç bir daha kabul edilmez.
  Oturum yokken çıkış da başarılı döner. Bir kullanıcının birden fazla eşzamanlı oturumu olabilir;
  çıkış yalnızca o tarayıcının oturumunu kapatır. Oturumu olan bir tarayıcı yeniden giriş yaparsa
  eski oturumu silinir.
- R-10: Giriş, çıkış ve sağlık kontrolü dışındaki her API uç noktası geçerli bir oturum ister;
  yoksa `401` ve standart hata gövdesi döner. Oturumlu kullanıcı kendi bilgisini (ad, kullanıcı
  adı, rol) alabilir.
- R-11: Durum değiştiren istekler (giriş, çıkış) yalnızca JSON gövdeli istekleri kabul eder
  (SameSite ile birlikte CSRF koruması).

## User experience

- Flow: Kullanıcı başlangıç sayfasını açar → oturum yoksa **giriş formu** görünür → kullanıcı adı
  ve parolayı girip "Giriş yap"a basar (veya Enter) → başarılıysa **karşılama** görünümü
  ("Hoş geldin, Ali Demir (Çalışan)" + **Çıkış** düğmesi) ve altında sistem durumu kartı → Çıkış'a
  basınca giriş formuna döner. Oturumu varken sayfayı yenileyen kullanıcı doğrudan karşılamayı
  görür.
- States:
  - **Giriş formu (boş):** "Kullanıcı adı" ve "Parola" alanları (görünür etiketlerle), "Giriş yap"
    düğmesi.
  - **Gönderiliyor:** düğme devre dışı, metni "Giriş yapılıyor…".
  - **Hata:** form korunur (kullanıcı adı kalır, parola temizlenir), mesaj: "Kullanıcı adı veya
    parola hatalı."
  - **Sunucuya ulaşılamıyor:** mesaj: "Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin."
  - **Oturum süresi doldu:** oturum sona erdikten sonraki ilk istekte giriş formu, mesaj:
    "Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın."
  - **Başarı (karşılama):** "Hoş geldin, <Ad> (<Rol>)" + Çıkış düğmesi + sistem durumu kartı.
  - Yetki yok durumu: bu spec'te ayrı bir ekran yok (yetkisiz istek giriş formuna döner).
- Design reference: none — the flow above is the design.
- Accessibility: alanlar `label` ile bağlı; form klavyeyle tamamen kullanılabilir (Tab, Enter);
  hata ve durum mesajları `aria-live="polite"` bölgede; parola alanı `type="password"` ve
  `autocomplete="current-password"`, kullanıcı adı `autocomplete="username"`.

## Constraints & out of scope

- Sensitive area: Onay yetkisi ve görünürlük (kimlik, BR-6 ve BR-8'in temeli).
- Split: proposed 0002 (kullanıcılar, parolalı giriş, oturum) + 0003 (brute force koruması:
  hesap kilidi 5 deneme / 15 dk, IP sınırı 20 deneme / 15 dk, kalıcı sayaçlar) — accepted by
  yunusemretapan, 2026-11-07, clarify gate. 0003, 0002 ship edildikten hemen sonra; arada yalnızca
  yerel demo çalıştırılır.
- Parola türetme üretimde OWASP'ın scrypt önerisine uygun parametrelerle çalışır (değerler planda);
  testlerde maliyet yapılandırmayla düşürülebilir, en az bir test üretim parametreleriyle doğrular.
- Yeni üçüncü taraf bağımlılık yok: parola türetme standart kütüphaneden, `.env` okuma
  Starlette'in yerleşik yapılandırma okuyucusundan.
- Bu spec bootstrap güvenlik duruşunu değiştirir: `docs/security.md` (AuthN/AuthZ, Secrets:
  `SESSION_SECRET` yerine `DEMO_PASSWORD`), `docs/architecture.md` (gerçek kimlik doğrulama artık
  kapsamda), `docs/domain.md` (üst yönetici istisnası: "Üst yönetici hariç her çalışanın tam bir
  yöneticisi vardır; üst yöneticinin izin talebi MVP kapsamı dışıdır.") güncellenir; B-1 kapanır.
- Out of scope: brute force koruması (0003); parola değiştirme/sıfırlama; çok faktörlü doğrulama;
  kullanıcı ekleme/düzenleme; "beni hatırla"; izin bakiyesi, talep, onay; HTTPS kurulumu.

## Acceptance criteria

- [x] AC-1 — Boş bir veri deposuyla ilk açılışta R-1 tablosundaki altı kullanıcı adları, rolleri ve yöneticileriyle oluşur; ikinci açılışta kullanıcı sayısı altı kalır.
- [x] AC-2 — `DEMO_PASSWORD` yoksa, 12 karakterden kısaysa, 128 karakterden uzunsa veya yaygın parolalar listesindeyse uygulama açılmaz ve parolayı yazmadan nedeni Türkçe bildirir; tam 12 ve tam 128 karakterlik geçerli bir parolayla açılır. Kullanıcı adına eşit bir parola politika tarafından reddedilir.
- [x] AC-3 — Veri deposunda hiçbir parola düz metin bulunmaz; aynı parolayı taşıyan iki kullanıcının saklanan değerleri birbirinden farklıdır.
- [x] AC-4 — Doğru kullanıcı adı (büyük/küçük harf farkıyla da) ve parolayla giriş başarılıdır: kullanıcının adı ve rolü döner ve `HttpOnly`, `SameSite=Lax` bir oturum çerezi verilir (`Secure` yapılandırmayla açıldığında çerezde bulunur).
- [x] AC-5 — Yanlış parola ve olmayan kullanıcı adı aynı `401` durumunu ve birebir aynı gövdeyi ("Kullanıcı adı veya parola hatalı.") döner; olmayan kullanıcıda da parola doğrulaması çalışır.
- [x] AC-6 — Oturum olmadan veya geçersiz/değiştirilmiş bir belirteçle kendi bilgisini isteyen kullanıcı `401`, `UNAUTHENTICATED` kodu ve standart hata gövdesi alır; sağlık kontrolü oturumsuz da çalışır. Veri deposunda oturum belirtecinin kendisi değil yalnızca özeti bulunur.
- [x] AC-7 — Oturum, 29 dakika aralıklı isteklerle 8 saate kadar geçerli kalır; 30 dakikadan uzun hareketsizlikten sonra ve açılışından 8 saat sonra (etkinliğe rağmen) `401` ve `SESSION_EXPIRED` kodu döner; süresi dolan oturum veri deposundan silinmiştir.
- [x] AC-8 — Çıkıştan sonra eski belirteç `401` alır; oturum yokken çıkış başarılı döner; iki ardışık girişte farklı belirteçler üretilir ve aynı tarayıcının önceki belirteci geçersizdir; aynı kullanıcının başka bir oturumu çıkıştan etkilenmez.
- [x] AC-9 — JSON olmayan bir gövdeyle (ör. form-encoded) gönderilen giriş isteği reddedilir ve oturum açılmaz.
- [x] AC-10 — Başlangıç sayfası User experience'taki durumları doğru metinle üretir: giriş formu, gönderiliyor, hata, sunucuya ulaşılamıyor, oturum süresi doldu ve karşılama ("Hoş geldin, <Ad> (<Rol>)" + Çıkış); alanlar etiketli ve doğru `autocomplete` değerlerini taşır.

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation)
- [x] `scripts/check` green
- [x] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [x] Docs / ADRs updated if behavior or architecture changed (`docs/security.md`, `docs/architecture.md`, `docs/domain.md`, README, `.env.example`, ADR 0001 sunucu tarafı oturum ve scrypt; B-1 kapatıldı)
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Evidence (VERIFY, HEAD f8e1585)
Full green: CHECK GREEN (full, 8 steps, 11 s) @c2a69d8 — https://github.com/yunusemretapan/leavemanagercoursedemo/actions/runs/42383208793
(HEAD yalnızca `specs/` kadar farklı) · QA doğrudan: CHECK GREEN (full, 8 steps, 47 s), HEAD içeriği, geçici kopya.
Yeniden üretim: `./scripts/check`. Hassas alan: her kriter QA'nın kasıtlı bozmalarıyla kırmızıya döndü (43 bozma, 42 kırmızı;
B4f: `lower()` tek başına kaldırılınca `COLLATE NOCASE` korumaya devam ediyor — ikisi birlikte kırmızı).

| Acceptance criterion | Evidence | Status |
|---|---|---|
| AC-1 | `test_first_start_seeds_six_demo_users_with_managers`, `test_second_start_keeps_six_users`; bozmalar: yanlış yönetici, dolu tablo koruması kaldırıldı → kırmızı | PASS |
| AC-2 | `test_policy_rejects_short_long_common_and_username`, `test_policy_accepts_12_and_128_chars`, `test_validate_demo_password_boundaries_and_no_echo`, `test_validate_demo_password_checks_every_demo_username`, `test_app_refuses_to_start_without_valid_demo_password`; gözlem: 129 karakter → çıkış kodu 2; bozmalar: alt/üst sınır, kara liste, yalnızca ilk kullanıcı, parola stderr'de → kırmızı | PASS |
| AC-3 | `test_hashes_differ_for_same_password_and_verify`, `test_verify_with_production_params`, `test_no_plaintext_password_in_database`; bozmalar: sabit salt, düz parola, N=2^14 → kırmızı | PASS |
| AC-4 | `test_login_success_case_insensitive_sets_session_cookie`, `test_secure_cookie_flag_when_configured`; bozmalar: HttpOnly, SameSite, Secure (iki yönde), harf duyarlılığı → kırmızı | PASS |
| AC-5 | `test_wrong_password_and_unknown_user_get_identical_401`, `test_unknown_user_still_verifies_password`; bozmalar: farklı gövde/mesaj, doğrulama atlandı → kırmızı | PASS |
| AC-6 | `test_me_without_or_with_tampered_token_is_unauthenticated`, `test_health_open_and_only_token_hash_stored`, `test_every_api_route_requires_session_except_the_allowlist`; bozmalar: 403, değiştirilmiş belirteç kabulü, ham belirteç saklama, health kapalı → kırmızı | PASS |
| AC-7 | `test_session_survives_activity_until_absolute_limit`, `test_idle_timeout_expires_and_deletes_session`, `test_absolute_timeout_expires_despite_activity`, `test_expired_session_returns_session_expired_code`; bozmalar: idle 60 dk, mutlak yok, touch yok, silme yok, sınır, hata kodu → kırmızı | PASS |
| AC-8 | `test_logout_invalidates_only_this_session`, `test_relogin_issues_new_token_and_drops_old`, `test_logout_ends_session_and_without_session_succeeds`, `test_relogin_in_same_browser_invalidates_previous_token`; bozmalar: çıkış/yeniden giriş silmiyor, tüm oturumlar siliniyor, oturumsuz çıkış 401, sabit belirteç → kırmızı | PASS |
| AC-9 | `test_form_encoded_login_is_rejected_without_session`, `test_json_login_without_content_type_is_rejected`, `test_non_json_logout_is_rejected_and_session_survives`; bozmalar: form ayrıştırma, `strict_content_type=False` → kırmızı | PASS |
| AC-10 | `web/tests/auth-view.test.js` (5), `test_index_page_has_labelled_login_form`; S-1…S-9b; 7 bozma → kırmızı | PASS |

UI: S-1 boş form · S-2 gönderiliyor · S-3 hata · S-4 sunucuya ulaşılamıyor · S-5 karşılama · S-6 oturumla yenileme · S-7 çıkış başarısız (F-6) · S-8 oturum süresi doldu · S-9a yönetici karşılaması · S-9b çıkış sonrası — S-1…S-9b agent-captured, judged by yunusemretapan at SHIP, 2026-11-07.

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 0 |
| Fix rounds | 2 |
| Review findings: real / noise / deferred | 11 / 2 / 0 |
| Regressions introduced | 0 |
| Bugs escaped to production | 0 (üretime çıkmıyor) |
