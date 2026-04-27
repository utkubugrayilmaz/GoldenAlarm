"""
GoldenAlarm - Yapılandırma Dosyası
Tüm sabitler ve ayarlar burada tanımlanır.
"""

# ============ API AYARLARI ============
API_URL = "https://finans.truncgil.com/v4/today.json"
API_TIMEOUT = 15

# ============ KONTROL SIKLIĞI ============
CHECK_INTERVAL_MINUTES = 5

# ============ BİLDİRİM AYARLARI ============
BILDIRIM_ESIK = 1000  # Her 1000 TL değişimde takip bildirimi

# ============ DOSYA YOLLARI ============
ALARMS_FILE = "alarms.json"

# ============ ALTIN TÜRLERİ ============
ALTIN_TURLERI = {
    "HAS": {
        "ad": "Gram Has Altın",
        "emoji": "🥇",
        "birim": "gram"
    },
    "YIA": {
        "ad": "22 Ayar Bilezik",
        "emoji": "📿",
        "birim": "gram"
    },
    "CEYREKALTIN": {
        "ad": "Çeyrek Altın",
        "emoji": "🪙",
        "birim": "adet"
    },
    "YARIMALTIN": {
        "ad": "Yarım Altın",
        "emoji": "🪙",
        "birim": "adet"
    },
    "TAMALTIN": {
        "ad": "Tam Altın",
        "emoji": "🪙",
        "birim": "adet"
    },
    "CUMHURIYETALTINI": {
        "ad": "Cumhuriyet Altını",
        "emoji": "🏅",
        "birim": "adet"
    },
    "ATAALTIN": {
        "ad": "Ata Altın",
        "emoji": "🏅",
        "birim": "adet"
    },
    "RESATALTIN": {
        "ad": "Reşat Altın",
        "emoji": "🏅",
        "birim": "adet"
    },
    "HAMITALTIN": {
        "ad": "Hamit Altın",
        "emoji": "🏅",
        "birim": "adet"
    },
}

# ============ ÖZEL ÜRÜNLER ============
# Hesaplamalı ürünler (örn: 10gr bilezik = 22 ayar × 10)
OZEL_URUNLER = {
    "AJDA_5GR": {
        "ad": "5gr Ajda Bilezik",
        "emoji": "📿",
        "kaynak": "YIA",
        "carpan": 5
    },
    "AJDA_10GR": {
        "ad": "10gr Ajda Bilezik",
        "emoji": "📿",
        "kaynak": "YIA",
        "carpan": 10
    },
    "AJDA_15GR": {
        "ad": "15gr Ajda Bilezik",
        "emoji": "📿",
        "kaynak": "YIA",
        "carpan": 15
    },
    "AJDA_20GR": {
        "ad": "20gr Ajda Bilezik",
        "emoji": "📿",
        "kaynak": "YIA",
        "carpan": 20
    },
}

# ============ TÜM ÜRÜNLER (Birleşik) ============
TUM_URUNLER = {**ALTIN_TURLERI, **OZEL_URUNLER}