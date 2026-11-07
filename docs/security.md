# Security

> Bootstrap 2026-11-07'de dolduruldu. Baseline rules agents must honor in every plan and review.

## Secrets
- Secrets never enter the repo, specs, prompts, or chat. `.env` is gitignored; provide `.env.example`.
- Agents never print secret values, even when debugging.
- Tek sır: `DEMO_PASSWORD` (demo kullanıcıların başlangıç parolası) — önce ortam değişkeni, yoksa
  `.env` (Starlette `Config`); `.env.example`'da yalnızca adı ve politika notu. Testler sabit bir test
  değeri kullanır ve `LEAVE_ENV_FILE` ile `.env`'i devre dışı bırakır.
- Uygulama `DEMO_PASSWORD` yoksa veya parola politikasına uymuyorsa açılmayı reddeder; hata mesajı
  nedeni söyler, parolayı asla yazmaz. (Spec 0002 öncesindeki `SESSION_SECRET` kaldırıldı — ADR 0001.)

## Input & output
- Tüm girdi sınırda (`app/api`) Pydantic şemalarıyla doğrulanır; tarih alanları strict `YYYY-MM-DD`;
  serbest metin alanlarının (açıklama, red gerekçesi) uzunluk sınırı vardır.
- SQL yalnızca parametreli sorgularla (`?`); string birleştirme/f-string ile SQL yasak (Ruff `S608`).
- **XSS:** görünüm fonksiyonları HTML string ürettiği için kullanıcı kaynaklı her değer tek bir
  `escapeHtml()` fonksiyonundan geçer (testli). Kaçışlanmamış veri `innerHTML`'e yazılmaz;
  düz metin için `textContent` tercih edilir.
- Hata yanıtlarında stack trace, SQL, dosya yolu, iç exception mesajı sızmaz (`docs/conventions.md`
  "Error handling"). Görme yetkisi olmayan kayıt `404` döner (varlığı sızdırılmaz, BR-8).
- CORS kapalı: tek origin (API ve statik dosyalar aynı süreçten).

## AuthN / AuthZ
- **AuthN — kullanıcı adı + parola** (spec 0002, ADR 0001):
  - Kullanıcı adı kırpılır ve büyük/küçük harf duyarsızdır. Kullanıcı listesi hiçbir yerde sunulmaz.
  - **Parola politikası** (NIST SP 800-63B): 12–128 karakter (Unicode karakter sayısı), kullanıcı
    adına eşit olamaz, `app/business/common_passwords.txt` kara listesinde olamaz; karakter sınıfı
    zorunluluğu yok; parola kırpılmaz. Bir parolanın belirlendiği her noktada uygulanır.
  - **Saklama:** scrypt (OWASP: N=2^17, r=8, p=1), kullanıcıya özgü 16 bayt rastgele salt;
    doğrulama sabit zamanlı (`hmac.compare_digest`). Maliyet ortam değişkeniyle düşürülemez.
  - **Başarısız giriş** tek ve genel: `401 INVALID_CREDENTIALS` "Kullanıcı adı veya parola hatalı.";
    olmayan kullanıcıda da (sahte hash ile) parola doğrulaması yapılır.
  - **Oturum sunucu tarafında:** çerezde rastgele 32 bayt belirteç (`lm_session`, `HttpOnly`,
    `SameSite=Lax`, `Secure` = `LEAVE_COOKIE_SECURE`), veri deposunda yalnızca SHA-256 özeti.
    Mutlak süre 8 saat, hareketsizlik 30 dakika (`Clock`); süresi dolan `401 SESSION_EXPIRED`,
    belirteçsiz/geçersiz `401 UNAUTHENTICATED`. Her girişte yeni belirteç (session fixation yok);
    çıkış oturumu sunucuda siler.
  - **CSRF:** durum değiştiren istekler yalnızca JSON gövde kabul eder + `SameSite=Lax`.
  - **Brute force koruması:** spec 0003 (hesap kilidi, IP sınırı) — 0002 ile 0003 arasında yalnızca
    yerel demo çalıştırılır.
- **Default deny:** açık uç noktalar yalnızca `POST /api/auth/login`, `POST /api/auth/logout` ve
  `GET /api/health` (kişisel veri içermez). Diğer her `/api/*` uç noktası oturum ister; yoksa `401`.
- **AuthZ `app/business` katmanında uygulanır**, router'da değil: her kullanım senaryosu çağıran
  kullanıcıyı parametre olarak alır ve BR-6 (yalnızca talep sahibinin yöneticisi karar verir, kendi
  talebine karar yok) ve BR-8 (görünürlük) kurallarını kendisi denetler. Hiçbir router bu kontrolü
  atlayamaz; kurallar unit testle kanıtlanır.
- Çalışan yalnızca kendi talep ve bakiyesini görür; yönetici ayrıca kendi ekibinin taleplerini.

## Dependencies
- Yeni bir bağımlılık (runtime veya geliştirme) yalnızca **onaylanmış bir planda**, adı ve gerekçesiyle
  eklenir; onayı plan onayıyla insan verir. Plan dışı bağımlılık = sapma (R-07).
- Kontrol: izin verici lisans (MIT, BSD, Apache-2.0; diğerleri ADR ister), aktif bakım (son 12 ayda
  sürüm), bilinen CVE yok.
- Kesin sürümler `requirements.lock`'ta kilitli; kilit dosyası değişikliği aynı commit'te.
- `pip-audit` (kilitli bağımlılıklarda bilinen CVE) yalnızca full profilde koşar ve ağ gerektirdiği için
  bir `requires` satırı taşır; fast profil çevrimdışı ve deterministik kalır.
- Frontend'de üçüncü taraf JS yok (CDN dahil).

## Review lens
Security is a mandatory dimension of every independent review (see `prompts/review.md`), not a
separate afterthought phase.
