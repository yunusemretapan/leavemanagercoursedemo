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
  - **Brute force koruması** (spec 0003, ADR 0002):
    - Kullanıcı adı başına son 15 dk'da 5 başarısız deneme → 15 dk kilit (doğru parola da reddedilir,
      parola doğrulanmaz; kilit sırasındaki denemeler sayılmaz, kilidi uzatmaz). Başarılı giriş
      kullanıcı adı sayacını sıfırlar ve o kullanıcı adının kilidini kaldırır (kilit, deneme
      kabul edildikten sonra eşzamanlı başarısızlıklarla oluşmuş olabilir; parola doğrudur). Var olmayan kullanıcı adları aynen sayılır ve kilitlenir.
    - İstemci adresi başına son 15 dk'da 20 başarısız deneme → o adresin her denemesi reddedilir;
      başarılı giriş adres sayacını sıfırlamaz. Adres yalnızca doğrudan bağlantıdan alınır,
      `X-Forwarded-For` okunmaz.
    - Reddedilen deneme: `429 TOO_MANY_ATTEMPTS`, tek mesaj (hesap/adres ayrımı sızmaz),
      `Retry-After` saniye. Deneme doğrulamadan önce `BEGIN IMMEDIATE` içinde sayılır (eşzamanlı
      denemeler sınırı aşamaz). Sayaçlar veri deposunda, yeniden başlatmada korunur.
    - Kilit açık oturumları sonlandırmaz. Kilit başlangıcı `app.auth` logger'ına `WARNING` olarak
      yazılır (kullanıcı adı, adres, zaman; parola asla).
- **Default deny:** açık uç noktalar yalnızca `POST /api/auth/login`, `POST /api/auth/logout` ve
  `GET /api/health` (kişisel veri içermez). Diğer her `/api/*` uç noktası oturum ister; yoksa `401`.
  Bu, `test_every_api_route_requires_session_except_the_allowlist` ile FastAPI'nin OpenAPI rota
  envanteri üzerinden denetlenir; bu yüzden `app/` hiçbir rotada `include_in_schema` kullanmaz
  (`test_no_route_hides_from_the_inventory`).
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
