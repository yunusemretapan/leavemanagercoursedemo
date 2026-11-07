# Spec 0002 — kullanıcılar, parolalı giriş ve oturum

- Status: In progress
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

- [ ] AC-1 — Boş bir veri deposuyla ilk açılışta R-1 tablosundaki altı kullanıcı adları, rolleri ve yöneticileriyle oluşur; ikinci açılışta kullanıcı sayısı altı kalır.
- [ ] AC-2 — `DEMO_PASSWORD` yoksa, 12 karakterden kısaysa, 128 karakterden uzunsa veya yaygın parolalar listesindeyse uygulama açılmaz ve parolayı yazmadan nedeni Türkçe bildirir; tam 12 ve tam 128 karakterlik geçerli bir parolayla açılır. Kullanıcı adına eşit bir parola politika tarafından reddedilir.
- [ ] AC-3 — Veri deposunda hiçbir parola düz metin bulunmaz; aynı parolayı taşıyan iki kullanıcının saklanan değerleri birbirinden farklıdır.
- [ ] AC-4 — Doğru kullanıcı adı (büyük/küçük harf farkıyla da) ve parolayla giriş başarılıdır: kullanıcının adı ve rolü döner ve `HttpOnly`, `SameSite=Lax` bir oturum çerezi verilir (`Secure` yapılandırmayla açıldığında çerezde bulunur).
- [ ] AC-5 — Yanlış parola ve olmayan kullanıcı adı aynı `401` durumunu ve birebir aynı gövdeyi ("Kullanıcı adı veya parola hatalı.") döner; olmayan kullanıcıda da parola doğrulaması çalışır.
- [ ] AC-6 — Oturum olmadan veya geçersiz/değiştirilmiş bir belirteçle kendi bilgisini isteyen kullanıcı `401`, `UNAUTHENTICATED` kodu ve standart hata gövdesi alır; sağlık kontrolü oturumsuz da çalışır. Veri deposunda oturum belirtecinin kendisi değil yalnızca özeti bulunur.
- [ ] AC-7 — Oturum, 29 dakika aralıklı isteklerle 8 saate kadar geçerli kalır; 30 dakikadan uzun hareketsizlikten sonra ve açılışından 8 saat sonra (etkinliğe rağmen) `401` ve `SESSION_EXPIRED` kodu döner; süresi dolan oturum veri deposundan silinmiştir.
- [ ] AC-8 — Çıkıştan sonra eski belirteç `401` alır; oturum yokken çıkış başarılı döner; iki ardışık girişte farklı belirteçler üretilir ve aynı tarayıcının önceki belirteci geçersizdir; aynı kullanıcının başka bir oturumu çıkıştan etkilenmez.
- [ ] AC-9 — JSON olmayan bir gövdeyle (ör. form-encoded) gönderilen giriş isteği reddedilir ve oturum açılmaz.
- [ ] AC-10 — Başlangıç sayfası User experience'taki durumları doğru metinle üretir: giriş formu, gönderiliyor, hata, sunucuya ulaşılamıyor, oturum süresi doldu ve karşılama ("Hoş geldin, <Ad> (<Rol>)" + Çıkış); alanlar etiketli ve doğru `autocomplete` değerlerini taşır.

## Definition of Done
- [ ] Every acceptance criterion mapped to proof (test or reproducible observation)
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [ ] Docs / ADRs updated if behavior or architecture changed (`docs/security.md`, `docs/architecture.md`, `docs/domain.md`, README, `.env.example`, ADR 0001 sunucu tarafı oturum ve scrypt; B-1 kapatıldı)
- [ ] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | |
| Fix rounds | |
| Review findings: real / noise / deferred | |
| Regressions introduced | |
| Bugs escaped to production | |
