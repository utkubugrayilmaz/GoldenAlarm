# GoldenAlarm

Telegram üzerinden altın fiyatlarını anlık olarak takip etmenizi ve özel fiyat alarmları kurmanızı sağlayan bot uygulaması.

## Özellikler

- Anlık altın fiyatları takibi (Gram, Çeyrek, Yarım, Tam, Cumhuriyet, Ata, Reşat).
- Özel gramaj hesaplamaları (5gr, 10gr, 15gr, 20gr Ajda Bilezik).
- Yön bazlı fiyat alarmı kurabilme (Yukarı/Aşağı).
- Belirli aralıklarla (ör. her 1.000 TL değişimde) takip bildirimleri.
- 5 dakikada bir otomatik arka plan kontrolü.

## Telegram Komutları

| Komut | Açıklama |
|---------|-------------|
| `/start` | Botu başlatır ve karşılama mesajını gösterir. |
| `/fiyat` | Güncel altın fiyatlarını listeler. |
| `/alarm` | Yeni bir fiyat alarmı kurar. |
| `/alarmlar`| Mevcut alarmları listeler. |
| `/sil` | Belirtilen alarmı siler. |
| `/yardim` | Komutlar hakkında yardım menüsünü görüntüler. |

## Kurulum

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/KULLANICI_ADIN/GoldenAlarm.git
cd GoldenAlarm
```

### 2. Sanal Ortam (Virtual Environment) Oluşturun

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Çevresel Değişkenleri Ayarlayın

```bash
cp .env.example .env
```
`.env` dosyasını bir metin editörüyle açarak gerekli API anahtarlarını ve ayarları doldurun.

### 5. Botu Çalıştırın

```bash
python main.py
```

## Render.com Üzerinde Canlıya Alma (Deployment)

1. Render.com üzerinde yeni bir **Background Worker** oluşturun.
2. GitHub deponuzu bağlayın.
3. Aşağıdaki **Environment Variables** (Ortam Değişkenleri) tanımlarını ekleyin:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Uygulamayı deploy edin.

## Veri Kaynağı

Bu projede finansal veriler, ücretsiz ve limit gerektirmeyen [Trunçgil Finans API](https://finans.truncgil.com/) üzerinden sağlanmaktadır.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.

## Geliştirici

Utku Buğra Yılmaz
