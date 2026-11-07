# ADR 0001 — Parolalı giriş: sunucu tarafı oturum ve scrypt

- Status: Accepted
- Date: 2026-11-07

## Context

Bootstrap'ta (2026-11-07) güvenlik duruşu "yalnızca demo" idi: parola yok, kullanıcı seçimi ve
Starlette `SessionMiddleware` ile imzalı çerez (`SESSION_SECRET`); gerçek kimlik doğrulama B-1 ile
ertelenmişti. Spec 0002'nin clarify kapısında ürün sahibi giriş kimliği, parola kriterleri, oturum
süresi ve kaba kuvvet durumlarının "doğru şekilde" yönetilmesini istedi. İzin akışının (BR-6 onay
yetkisi, BR-8 görünürlük) güvenilir bir kimliğe dayanması gerekiyor. Kısıtlar: kurs demosu, tek
süreç, SQLite, yeni bağımlılık eklememe eğilimi (`docs/security.md` "Dependencies").

## Decision

Kullanıcı adı + parolayla giriş; parolalar standart kütüphanenin `hashlib.scrypt`'iyle (OWASP
temel değerleri N=2^17, r=8, p=1, kullanıcıya özgü 16 bayt salt) saklanır ve sabit zamanlı
doğrulanır; oturumlar **sunucu tarafında** tutulur: çerezde rastgele 32 baytlık belirteç, veri
deposunda yalnızca SHA-256 özeti; 8 saat mutlak, 30 dakika hareketsizlik süresi. `SESSION_SECRET`
ve imzalı çerez kaldırılır; tek sır `DEMO_PASSWORD` olur. Brute force koruması spec 0003'tür.

## Consequences

- **Kazanç:** çıkış ve (0003'te) kilitlenme oturumu sunucuda gerçekten sonlandırır; çalınan bir
  çerez iptal edilebilir; veri deposu sızsa bile belirteçler ve parolalar doğrudan kullanılamaz;
  yönetilecek imza anahtarı yok; yeni bağımlılık yok.
- **Bedel:** her istekte oturum için bir veri deposu okuması ve yazması (`last_seen_at`); her giriş
  bu makinede ~1.3 sn ve ~128 MiB (kasıtlı maliyet); ilk açılışta altı demo hash'i (3 iş parçacığıyla
  ~4 sn); süresi dolmuş oturumların temizliği uygulamanın sorumluluğu (girişte ve fark edildiğinde).
- Bootstrap kararları değişti: `docs/security.md` AuthN/Secrets, `docs/architecture.md` kapsam dışı
  listesi; B-1 kapandı.

## Alternatives considered

- **İmzalı çerez (Starlette `SessionMiddleware`) + parola:** durumsuz ve basit, ama çıkış/kilit
  çerezi geçersiz kılamaz (süresi dolana dek geçerli); bir imza anahtarı yönetmek gerekir. Kaybetti:
  "doğru yönetim" isteği iptal edilebilir oturum gerektiriyor.
- **Argon2id (`argon2-cffi`):** OWASP'ın ilk tercihi, ama yeni (native) bir bağımlılık ve Windows
  derleme riski. scrypt OWASP'ın kabul ettiği eşdeğer bir seçenek ve standart kütüphanede. Kaybetti.
- **PBKDF2:** standart kütüphanede, ama bellek-zor değil (GPU saldırısına daha açık). Kaybetti.
- **Demo kullanıcı seçimi (parolasız) ile devam:** ürün sahibinin isteğiyle reddedildi.

## Revisit triggers

- Ürün gerçek kullanıcılara açılacaksa: SSO / çok faktörlü doğrulama, parola sıfırlama, HTTPS
  zorunluluğu (`LEAVE_COOKIE_SECURE=true`) ve Argon2id yeniden değerlendirilir.
- Giriş gecikmesi veya bellek kullanımı sorun olursa: scrypt parametreleri OWASP'ın eşdeğer
  tablosu içinde (ör. N=2^16, p=2) yeniden ayarlanır — düşürmek değil, dengelemek.
  Parametre değişikliği iki şey gerektirir: girişte eski parametreli hash'lerin yeniden hash'lenmesi
  ve sahte hash'in (olmayan kullanıcı) saklanan hash'lerle aynı maliyette kalması — aksi halde yanıt
  süresi kullanıcı adının varlığını sızdırır (R-6; review round 1 F-9).
- Birden fazla süreçle çalışma: oturum deposu ve SQLite eşzamanlılığı yeniden ele alınır.
