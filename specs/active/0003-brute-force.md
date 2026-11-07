# Spec 0003 — brute force koruması

- Status: In progress
- Mode: lite
- Plan: `specs/plans/0003-plan.md`
- Self-critique: done

## Intent

Parolalı giriş (spec 0002), sınırsız deneme yapılabildiği sürece tahmin saldırılarına açıktır. Bu
spec, bir hesaba veya tek bir kaynaktan yapılan art arda başarısız denemeleri sınırlayarak parola
tahminini pratik olmaktan çıkarır; kilit davranışı hangi kullanıcı adlarının var olduğunu ele
vermez ve sayaçlar uygulama yeniden başlasa da korunur. Başarı: 5 yanlış denemeden sonra hesap 15
dakika kilitlenir, tek kaynaktan 15 dakikada 20 başarısız denemeden sonra o kaynağın denemeleri
reddedilir; gerçek kullanıcı süre dolunca normal şekilde girer ve açık oturumu kilitten etkilenmez.
Bilinçli olarak yapılmayan: yönetici kilit açma, CAPTCHA, e-posta bildirimi, kalıcı hesap kilidi.

## Requirements

- R-1: **Hesap sınırı** — bir (normalleştirilmiş) kullanıcı adı için son 15 dakika içinde 5
  başarısız giriş olduğunda, 5. başarısızlık anından itibaren 15 dakika boyunca o kullanıcı adıyla
  yapılan her giriş denemesi — doğru parolayla bile — reddedilir. Kilit sırasında parola
  doğrulanmaz; kilit sırasındaki denemeler sayılmaz ve kilidi uzatmaz.
- R-1a: Sınırlar **eşzamanlı** denemelerde de aşılmaz: bir deneme, parola doğrulanmadan önce
  başarısız olarak kaydedilir; sınır denetimi ve bu kayıt tek bir veri deposu işleminde yapılır;
  giriş başarılı olursa kayıt silinir ve kullanıcı adı sayacı sıfırlanır. Başarısız bir deneme hem
  kullanıcı adı hem adres sayacına yazılır; `429` ile reddedilen veya doğrulama hatasıyla (`422`)
  dönen deneme hiçbir sayaca yazılmaz.
- R-2: Başarılı bir giriş, o kullanıcı adının başarısızlık sayacını sıfırlar. 15 dakikadan eski
  başarısızlıklar sayılmaz (kayan pencere).
- R-3: Var olmayan kullanıcı adları R-1/R-2'ye aynen tabidir; yanıtları, var olan bir kullanıcınınkiyle
  aynıdır (kilit, hesabın varlığını ele vermez).
- R-4: **Kaynak (IP) sınırı** — tek bir istemci adresinden son 15 dakika içinde 20 başarısız giriş
  olduğunda, o adresten gelen her giriş denemesi (hangi kullanıcı adıyla olursa olsun, doğru
  parolayla bile) pencere 20'nin altına inene kadar reddedilir. Başarılı giriş adres sayacını
  sıfırlamaz. Adres doğrudan bağlantıdan alınır; `X-Forwarded-For` ve benzeri başlıklara güvenilmez.
  Adres bilinmiyorsa tek bir `unknown` sayacı kullanılır.
- R-5: Reddedilen deneme `429`, `TOO_MANY_ATTEMPTS` kodu ve standart hata gövdesiyle döner; mesaj:
  "Çok fazla başarısız giriş denemesi. Lütfen 15 dakika sonra tekrar deneyin." Hesap kilidi ve
  adres sınırı için mesaj ve kod aynıdır. Yanıt, bir sonraki denemeye kadar kalan süreyi saniye
  olarak `Retry-After` başlığında taşır: iki sınır birden geçerliyse büyük olanı, tam saniyeye
  yukarı yuvarlanmış, en az 1. Arayüzdeki "15 dakika" metni sabit bir üst sınırdır.
- R-6: Sayaçlar ve kilitler veri deposunda tutulur; uygulama yeniden başladığında korunur. 15
  dakikadan eski kayıtlar her giriş denemesinde temizlenir.
- R-7: Kilit, kullanıcının açık oturumlarını sonlandırmaz; yalnızca yeni girişleri engeller.
- R-8: Bir hesap kilidi başladığında sunucu log'una bir uyarı satırı yazılır (`app.auth` logger'ı,
  `WARNING`): `account locked username=<ad> ip=<adres> at=<UTC ISO>`. Parola asla yazılmaz.

## User experience

- Flow: Kullanıcı giriş formunda sınır aşılınca formda kalır ve sınır mesajını görür; 15 dakika
  sonra normal şekilde giriş yapabilir.
- States:
  - **Çok fazla deneme:** form korunur (kullanıcı adı kalır, parola temizlenir), mesaj: "Çok fazla
    başarısız giriş denemesi. Lütfen 15 dakika sonra tekrar deneyin."
  - Diğer durumlar spec 0002'deki gibidir (değişmez).
- Design reference: none — the flow above is the design.
- Accessibility: mesaj mevcut `aria-live="polite"` bölgesinde duyurulur.

## Constraints & out of scope

- Sensitive area: Onay yetkisi ve görünürlük (kimliğin korunması; spec 0002'nin devamı).
- Parametreler spec 0002'nin bölme kararıyla sabittir: hesap 5 deneme / 15 dk, adres 20 deneme /
  15 dk, kalıcı sayaçlar.
- ADR 0001'in "(0003'te) kilitlenme oturumu sunucuda gerçekten sonlandırır" ifadesi R-7 ile
  değişir: yeni ADR 0002 bunu kayda geçirir (kabul edilmiş ADR düzenlenmez). ADR 0002 ayrıca
  istemci adresinin doğrudan bağlantıdan alındığını ve bir ters vekil eklenirse yeniden
  değerlendirileceğini yazar.
- Yeni üçüncü taraf bağımlılık yok.
- Out of scope: yönetici kilit açma, CAPTCHA, e-posta/SMS bildirimi, kalıcı kilit, kilit
  sırasında açık oturumların sonlandırılması, ters vekil arkasında gerçek istemci adresi.

## Acceptance criteria

- [ ] AC-1 — Bir kullanıcı adı için 5 başarısız denemeden sonraki deneme, doğru parolayla bile, `429` ve `TOO_MANY_ATTEMPTS` döner ve parola doğrulanmaz; 4 başarısız denemeden sonra doğru parolayla giriş başarılıdır; aynı kullanıcı adıyla eşzamanlı 10 yanlış denemeden en fazla 5'inde parola doğrulanır.
- [ ] AC-2 — 4 başarısız deneme, ardından başarılı giriş, ardından 4 başarısız deneme hesabı kilitlemez (başarı sayacı sıfırlar); 15 dakikadan eski başarısızlıklar sayılmaz.
- [ ] AC-3 — Kilit, 5. başarısızlıktan 15 dakika sonra kalkar ve doğru parolayla giriş başarılıdır; kilit sırasındaki denemeler kilidi uzatmaz.
- [ ] AC-4 — Var olmayan bir kullanıcı adı için 5 başarısız denemeden sonraki yanıt, var olan bir kullanıcınınkiyle aynı durumu, gövdeyi ve `Retry-After` değerini taşır.
- [ ] AC-5 — Tek bir adresten (farklı kullanıcı adlarıyla) 15 dakikada 20 başarısız denemeden sonra o adresin her giriş denemesi, doğru parolayla bile, `429` döner; başka bir adres etkilenmez; araya giren başarılı giriş adres sayacını sıfırlamaz; `X-Forwarded-For` başlığı adresi değiştirmez.
- [ ] AC-6 — `429` yanıtı standart gövdeyi, R-5'teki mesajı ve kalan süreyi saniye olarak taşıyan bir `Retry-After` başlığını içerir.
- [ ] AC-7 — Uygulama yeniden başladıktan sonra kilit ve sayaçlar geçerlidir; 15 dakikadan eski deneme kayıtları bir giriş denemesinden sonra veri deposunda bulunmaz.
- [ ] AC-8 — Hesabı kilitlenen kullanıcının kilitten önce açılmış oturumu geçerli kalır.
- [ ] AC-9 — Kilit başladığında log'a zamanı, normalleştirilmiş kullanıcı adını ve adresi içeren tek bir uyarı satırı yazılır; log çıktısında hiçbir denemenin parolası geçmez.
- [ ] AC-10 — Giriş formu `TOO_MANY_ATTEMPTS` yanıtında R-5'teki mesajı gösterir, kullanıcı adını korur ve parolayı temizler.

## Definition of Done
- [ ] Every acceptance criterion mapped to proof (test or reproducible observation)
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [ ] Docs / ADRs updated if behavior or architecture changed (`docs/security.md` brute force bölümü, ADR 0002)
- [ ] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | |
| Fix rounds | |
| Review findings: real / noise / deferred | |
| Regressions introduced | |
| Bugs escaped to production | |
