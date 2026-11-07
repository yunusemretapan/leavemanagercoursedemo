# Domain

> Bootstrap 2026-11-07'de dolduruldu. İş, insanlar ve ajanlar arasındaki ortak dil.
> Bir terim burada yoksa, yapay zekânın kendi anlamını uydurmasını bekleyin.

**Ürün:** Kurs demosu olarak küçük, uçtan uca bir izin yönetimi uygulaması. Çalışan izin talep
eder ve bakiyesini görür; yönetici ekibinin taleplerini onaylar veya reddeder. Amaç ANEW iş
akışını (spec → plan → build → review → verify) gerçekçi ama küçük bir alanda göstermek.
Üretime çıkmaz; gerçek kişisel veri tutulmaz (yalnızca seed edilmiş demo kullanıcılar).

## Ubiquitous language

| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Çalışan (`Employee`) | İzin talep eden kişi. Üst yönetici hariç her çalışanın tam bir yöneticisi vardır. | Yönetici de bir çalışandır (kendi izni için). Üst yöneticinin izin talebi MVP kapsamı dışıdır (spec 0002). |
| Yönetici (`Manager`) | Ekibindeki çalışanların taleplerini onaylar/reddeder. | İK/Admin rolü yok (kapsam dışı). |
| Ekip (`Team`) | Bir yöneticiye doğrudan bağlı çalışanlar. | Departman/organizasyon ağacı yok. |
| İzin talebi (`LeaveRequest`) | Başlangıç tarihi, bitiş tarihi (dahil), izin türü, isteğe bağlı açıklama. | "İzin" tek başına belirsizdir: talep mi, bakiye mi — açıkça söyleyin. |
| İzin türü (`LeaveType`) | MVP'de yalnızca **Yıllık izin** (`ANNUAL`). | Hastalık/mazeret izni sonraki spec. |
| İzin bakiyesi (`LeaveBalance`) | Çalışanın içinde bulunulan takvim yılı için kalan yıllık izin iş günü. | Onay anında düşer, talep anında değil (BR-3). |
| İş günü | Pazartesi–Cuma arası bir gün. | Resmî tatiller MVP'de iş günü sayılır. |
| Talep durumu (`RequestStatus`) | `PENDING` (Beklemede) → `APPROVED` (Onaylandı) / `REJECTED` (Reddedildi); `PENDING` → `CANCELLED` (İptal). | Kodda İngilizce enum değerleri, arayüzde Türkçe etiketler. |
| Karara bağlanmış talep | `APPROVED` veya `REJECTED` durumundaki talep. | `CANCELLED` karar değil, çalışan eylemidir. |
| Red gerekçesi | Yöneticinin reddederken yazdığı zorunlu metin. | |

## Business rules

- **BR-1:** İzin süresi iş günü olarak sayılır: başlangıç ve bitiş dahil, Cumartesi ve Pazar sayılmaz. Resmî tatiller MVP'de sayılır (tatil takvimi sonraki spec).
- **BR-2:** Her çalışanın yıllık izin hakkı takvim yılı başına sabit **14 iş günüdür**; kullanılmayan gün sonraki yıla devretmez. Kıdeme göre hak ediş yoktur.
- **BR-3:** Bakiye talebin **onaylandığı anda** düşer. Talep oluşturulurken, talebin gün sayısı + çalışanın `PENDING` taleplerinin gün sayısı + onaylı günler 14'ü aşıyorsa talep reddedilir (`InsufficientBalance`). Onay anında da bakiye yeniden kontrol edilir.
- **BR-4:** Aynı çalışanın `PENDING` veya `APPROVED` talepleri tarih aralığı olarak çakışamaz (tek ortak gün bile çakışmadır) (`OverlappingRequest`).
- **BR-5:** Başlangıç tarihi bugün veya sonrası olmalı; bitiş tarihi başlangıçtan önce olamaz. Talep en az bir iş günü içermelidir. "Bugün" enjekte edilen `Clock`'tan gelir.
- **BR-6:** Bir talebi yalnızca talep sahibinin yöneticisi onaylayabilir veya reddedebilir; kimse kendi talebini onaylayamaz/reddedemez (`NotAuthorized`). Reddetmek için gerekçe zorunludur.
- **BR-7:** Karara bağlanmış (`APPROVED`/`REJECTED`) veya `CANCELLED` bir talep değiştirilemez. Çalışan yalnızca kendi `PENDING` talebini iptal edebilir. Onaylı izni iptal etmek MVP kapsamı dışıdır.
- **BR-8:** Çalışan yalnızca kendi taleplerini ve bakiyesini görür; yönetici ayrıca ekibinin taleplerini görür. Görme yetkisi olmayan bir kayıt "bulunamadı" olarak döner (varlığı sızdırılmaz).

## Key domain invariants

- Bir çalışanın yıl içindeki onaylı izin günleri toplamı asla 14'ü aşamaz.
- Bir çalışanın `PENDING`/`APPROVED` talepleri asla çakışmaz.
- Hiçbir talep, talep sahibinin yöneticisi dışında biri tarafından karara bağlanmaz.
- Durum geçişleri yalnızca: `PENDING→APPROVED`, `PENDING→REJECTED`, `PENDING→CANCELLED`. Başka geçiş yoktur.

## Sensitive areas

- **İzin bakiyesi hesabı** (BR-1, BR-2, BR-3) — hata, çalışanın hak kaybına veya fazla izne yol açar.
- **Onay yetkisi ve görünürlük** (BR-6, BR-8) — hata, yetkisiz onay veya başkasının verisinin görülmesi demektir.

Bu alanlara dokunan spec, Constraints bölümünde `Sensitive area: <ad>` yazar; lite modda da
clarify kapısı sorulur, her fix round yeniden incelenir, her kriter kasıtlı bir bozmayla kırmızı
olarak kanıtlanır (`workflows/README.md`, Modes).
