# GoldenAlarm

*(Türkçe dokümantasyon aşağıdadır / Turkish documentation is below)*

A Telegram bot application that allows you to instantly track gold prices and set custom price alarms.

## Features (EN)

- Real-time gold price tracking (Gram, Quarter, Half, Full, Republic, Ata, Reşat).
- Custom weight calculations (5g, 10g, 15g, 20g Ajda Bracelets).
- Direction-based price alarm setting (Up/Down).
- Tracking notifications at specific intervals (e.g., every 1,000 TRY change).
- Automatic background checks every 5 minutes.

## Telegram Commands (EN)

| Command | Description |
|---------|-------------|
| `/start` | Starts the bot and displays the welcome message. |
| `/fiyat` | Lists current gold prices. |
| `/alarm` | Sets a new price alarm. |
| `/alarmlar`| Lists existing alarms. |
| `/sil` | Deletes a specified alarm. |
| `/yardim` | Displays the help menu for commands. |

## Installation (EN)

### 1. Clone the Repository

```bash
git clone https://github.com/KULLANICI_ADIN/GoldenAlarm.git
cd GoldenAlarm
```

### 2. Create a Virtual Environment

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

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
cp .env.example .env
```
Open the `.env` file with a text editor and fill in the necessary API keys and settings.

### 5. Run the Bot

```bash
python main.py
```

## Deployment on Render.com (EN)

1. Create a new **Background Worker** on Render.com.
2. Connect your GitHub repository.
3. Add the following **Environment Variables**:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Deploy the application.

## Data Source (EN)

Financial data in this project is provided via the free and unmetered [Trunçgil Finans API](https://finans.truncgil.com/).

## License (EN)

This project is licensed under the MIT License.

---

# GoldenAlarm (TR)

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

## Geliştirici / Developer

Utku Buğra Yılmaz
