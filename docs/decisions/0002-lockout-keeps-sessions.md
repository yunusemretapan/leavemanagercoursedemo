# ADR 0002 — Brute force kilidi oturumları sonlandırmaz; istemci adresi doğrudan bağlantıdır

- Status: Accepted
- Date: 2026-11-07

## Context

Spec 0003 parolalı girişe (ADR 0001) kaba kuvvet koruması ekliyor: kullanıcı adı başına 5 başarısız
deneme / 15 dk kilit, istemci adresi başına 15 dk'da 20 başarısız deneme. ADR 0001 "Consequences"
bölümü, "(0003'te) kilitlenme oturumu sunucuda gerçekten sonlandırır" diyerek kilidin açık
oturumları da kapatacağını öngörmüştü. Spec 0003'ün clarify kapısında bunun bir saldırı aracı
olduğu görüldü: kilidi tetiklemek için yalnızca kullanıcı adını bilmek yeterli. Ayrıca adres
sınırı için istemci adresinin nereden okunacağına karar vermek gerekiyor; uygulamanın önünde ters
vekil (reverse proxy) yok.

## Decision

1. Hesap kilidi yalnızca **yeni girişleri** engeller; kullanıcının açık oturumları geçerli kalır.
   Bu, ADR 0001'in yukarıdaki ifadesinin yerine geçer (ADR 0001'in geri kalanı geçerli).
2. İstemci adresi **doğrudan bağlantıdan** (`request.client.host`) alınır; `X-Forwarded-For` ve
   benzeri başlıklara güvenilmez. Adres bilinmiyorsa tek bir `unknown` sayacı kullanılır.
3. Bir deneme parola doğrulanmadan önce başarısız sayılır; sınır denetimi ve bu kayıt tek bir
   `BEGIN IMMEDIATE` işlemindedir (eşzamanlı denemeler sınırı aşamaz).

## Consequences

- **Kazanç:** saldırgan, kullanıcı adını bilerek gerçek kullanıcıyı sistemden atamaz; yalnızca yeni
  girişini 15 dakika geciktirebilir. Başlık sahteciliğiyle adres sınırı aşılamaz. Eşzamanlı istek
  yağmuru kilitten önce en fazla 5 tahmin yaptırabilir.
- **Bedel / kalan risk:** kullanıcı adını bilen biri hesabı her 15 dakikada bir yeniden kilitleyerek
  yeni girişleri sürekli engelleyebilir (kilit uzamaz, ama yenilenebilir); adres sınırı bunu
  tek kaynaktan sınırlar. Paylaşılan bir adresin (NAT) arkasındaki kullanıcılar birbirinin adres
  sayacını etkiler. Doğrulama sırasında çöken bir süreç denemeyi başarısız olarak bırakır (güvenli
  taraf). Her giriş denemesi veri deposuna bir yazma kilidi alır.

## Alternatives considered

- **Kilitte oturumları da sonlandırmak (ADR 0001'in öngörüsü):** saldırgana "kullanıcıyı at" düğmesi
  verir; brute force denemesi mevcut oturumun ele geçirildiği anlamına gelmez. Kaybetti.
- **`X-Forwarded-For`'a güvenmek:** vekil yokken herkes başlığı uydurarak sınırı aşar. Kaybetti.
- **Doğrulamadan sonra saymak:** eşzamanlı istekler kilit oluşmadan önce sınırsız tahmin yapar
  (scrypt ~1.3 sn). Kaybetti.
- **Bellek içi sayaç:** yeniden başlatmada sıfırlanır (spec 0003 R-6 kalıcılık istiyor). Kaybetti.

## Revisit triggers

- Uygulamanın önüne bir ters vekil eklenirse: güvenilen vekil listesiyle gerçek istemci adresi
  okunmalı (aksi halde tüm istemciler vekilin tek adres sayacını paylaşır).
- Kilidin sürekli yenilenmesi gerçek kullanıcıları etkilemeye başlarsa: CAPTCHA, cihaz tanıma veya
  kademeli gecikme değerlendirilir.
- Birden fazla süreç / sunucu: sayaçlar paylaşılan bir depoya taşınmalı.
