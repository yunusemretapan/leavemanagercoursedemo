# Security

> Bootstrap 2026-11-07'de dolduruldu. Baseline rules agents must honor in every plan and review.

## Secrets
- Secrets never enter the repo, specs, prompts, or chat. `.env` is gitignored; provide `.env.example`.
- Agents never print secret values, even when debugging.
- Tek sır: `SESSION_SECRET` (oturum çerezi imza anahtarı) — `.env`'den okunur; `.env.example`'da yalnızca
  adı ve "uzun rastgele bir değer üretin" notu. Testler sabit bir test anahtarı kullanır, `.env` okumaz.
- Uygulama `SESSION_SECRET` yoksa açılmayı reddeder (sessiz varsayılan anahtar yok).

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
- **AuthN — yalnızca demo:** parola yok. Seed edilmiş kullanıcılar (ör. 2 yönetici, 4 çalışan);
  giriş ekranında kullanıcı seçilir, sunucu imzalı bir oturum çerezi verir (Starlette
  `SessionMiddleware`, `HttpOnly`, `SameSite=Lax`). Gerçek kimlik doğrulama kapsam dışıdır
  (`specs/backlog.md`). Bu mekanizma üretim için uygun değildir ve öyle sunulmaz.
- **Default deny:** giriş uç noktası dışındaki her `/api/*` uç noktası oturum ister; yoksa `401`.
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
