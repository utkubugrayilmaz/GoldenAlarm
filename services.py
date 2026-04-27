"""
GoldenAlarm - Servis Katmanı
API bağlantısı ve Alarm yönetimi
"""

import json
import os
import re
from datetime import datetime
from typing import Optional, Dict, List, Any

import requests
import urllib3

# SSL uyarılarını sustur (🧹 Fix #2)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import (
    API_URL,
    API_TIMEOUT,
    ALARMS_FILE,
    ALTIN_TURLERI,
    OZEL_URUNLER,
    TUM_URUNLER,
    BILDIRIM_ESIK
)


# ============================================================
#                      YARDIMCI FONKSİYONLAR
# ============================================================

def parse_turkish_float(value) -> float:
    """
    Türk formatındaki sayıyı float'a çevir (🚨 Fix #1)
    Örnekler:
        "6.232,12" -> 6232.12
        "6232.12"  -> 6232.12
        6232.12    -> 6232.12
        "6232"     -> 6232.0
    """
    if value is None:
        return 0.0

    # Zaten sayı ise direkt döndür
    if isinstance(value, (int, float)):
        return float(value)

    # String ise temizle
    if isinstance(value, str):
        value = value.strip()

        if not value:
            return 0.0

        # Türk formatı kontrolü: "6.232,12" (nokta binlik, virgül ondalık)
        if "," in value and "." in value:
            # Noktaları kaldır (binlik ayracı), virgülü noktaya çevir
            value = value.replace(".", "").replace(",", ".")
        elif "," in value:
            # Sadece virgül var, ondalık ayracı olarak kullanılmış
            value = value.replace(",", ".")
        # else: Sadece nokta var veya hiç ayraç yok, zaten doğru format

        try:
            return float(value)
        except ValueError:
            # Sayıya çevrilemezse 0 döndür
            return 0.0

    return 0.0


# ============================================================
#                      API SERVİSİ
# ============================================================

class GoldAPIService:
    """Altın fiyatları API servisi - Fallback destekli"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Connection": "keep-alive",
        })
        self.session.verify = False
        self.last_data: Optional[Dict] = None
        self.last_update: Optional[datetime] = None
        self.active_api: str = "truncgil"

    def fetch_prices(self) -> Dict[str, Any]:
        """API'den güncel fiyatları çek - fallback destekli"""

        # Önce Truncgil dene
        result = self._fetch_truncgil()
        if result["success"]:
            self.active_api = "truncgil"
            return result

        # Truncgil başarısız, BigPara dene
        result = self._fetch_bigpara()
        if result["success"]:
            self.active_api = "bigpara"
            return result

        # İkisi de başarısız
        return {"success": False, "error": "Tüm API'ler başarısız oldu. Lütfen daha sonra tekrar dene."}

    def _fetch_truncgil(self) -> Dict[str, Any]:
        """Truncgil API'den veri çek"""
        try:
            response = self.session.get(
                "https://finans.truncgil.com/v4/today.json",
                timeout=API_TIMEOUT
            )
            response.raise_for_status()

            # JSON parse öncesi kontrol
            text = response.text
            if not text.strip().endswith("}"):
                return {"success": False, "error": "Truncgil: Eksik JSON"}

            data = response.json()
            self.last_data = self._normalize_truncgil(data)
            self.last_update = datetime.now()

            return {"success": True, "data": self.last_data}

        except Exception as e:
            return {"success": False, "error": f"Truncgil: {str(e)}"}

    def _fetch_bigpara(self) -> Dict[str, Any]:
        """BigPara API'den veri çek (yedek)"""
        try:
            response = self.session.get(
                "https://api.bigpara.hurriyet.com.tr/altin/headerlist/anasayfa",
                timeout=API_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            self.last_data = self._normalize_bigpara(data)
            self.last_update = datetime.now()

            return {"success": True, "data": self.last_data}

        except Exception as e:
            return {"success": False, "error": f"BigPara: {str(e)}"}

    def _normalize_truncgil(self, data: Dict) -> Dict:
        """Truncgil verisini standart formata çevir"""
        # Zaten doğru formatta, direkt döndür
        return data

    def _normalize_bigpara(self, data: Dict) -> Dict:
        """BigPara verisini standart formata çevir"""
        normalized = {
            "Update_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # BigPara -> Truncgil format eşleştirmesi
        mapping = {
            "ALTIN": "HAS",
            "CEYREK_YENI": "CEYREKALTIN",
            "YARIM_YENI": "YARIMALTIN",
            "TEK_YENI": "TAMALTIN",
            "CUMHURIYET": "CUMHURIYETALTINI",
            "ATA_YENI": "ATAALTIN",
            "RESAT_YENI": "RESATALTIN",
            "HAMIT_YENI": "HAMITALTIN",
            "BILEZIK": "YIA",
        }

        if "data" in data:
            for item in data["data"]:
                kod = item.get("kod", "")
                if kod in mapping:
                    normalized[mapping[kod]] = {
                        "Buying": parse_turkish_float(item.get("alis")),
                        "Selling": parse_turkish_float(item.get("satis")),
                        "Change": parse_turkish_float(item.get("degisimYuzde"))
                    }

        return normalized

    def _reset_session(self):
        """Session'ı sıfırla"""
        self.session.close()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Connection": "keep-alive",
        })
        self.session.verify = False

    def get_price(self, urun_kodu: str, data: Optional[Dict] = None) -> Optional[float]:
        """Belirli bir ürünün fiyatını hesapla"""
        if data is None:
            data = self.last_data

        if data is None:
            return None

        # Özel ürün mü kontrol et
        if urun_kodu in OZEL_URUNLER:
            ozel = OZEL_URUNLER[urun_kodu]
            kaynak = ozel["kaynak"]
            carpan = ozel["carpan"]

            if kaynak in data:
                buying = data[kaynak].get("Buying", 0)
                return parse_turkish_float(buying) * carpan
            return None

        # Normal altın
        if urun_kodu in data:
            buying = data[urun_kodu].get("Buying", 0)
            return parse_turkish_float(buying)

        return None

    def get_all_prices(self, data: Optional[Dict] = None) -> Dict[str, Dict]:
        """Tüm ürün fiyatlarını getir"""
        if data is None:
            data = self.last_data

        if data is None:
            return {}

        prices = {}

        for kod, bilgi in TUM_URUNLER.items():
            fiyat = self.get_price(kod, data)
            if fiyat is not None:
                prices[kod] = {
                    "ad": bilgi["ad"],
                    "emoji": bilgi["emoji"],
                    "fiyat": fiyat
                }

        return prices

    def get_update_time(self, data: Optional[Dict] = None) -> str:
        """Son güncelleme zamanını getir"""
        if data is None:
            data = self.last_data

        if data and "Update_Date" in data:
            return data["Update_Date"]

        return "Bilinmiyor"


# ============================================================
#                    ALARM SERVİSİ
# ============================================================

class AlarmService:
    """Alarm yönetim servisi"""

    def __init__(self):
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Alarm dosyasının varlığını kontrol et"""
        if not os.path.exists(ALARMS_FILE):
            self._save([])

    def _load(self) -> List[Dict]:
        """Alarmları dosyadan yükle"""
        try:
            with open(ALARMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save(self, alarms: List[Dict]):
        """Alarmları dosyaya kaydet"""
        with open(ALARMS_FILE, "w", encoding="utf-8") as f:
            json.dump(alarms, f, ensure_ascii=False, indent=2)

    def _generate_id(self, alarms: List[Dict]) -> int:
        """Yeni alarm için benzersiz ID üret"""
        if not alarms:
            return 1
        return max(a["id"] for a in alarms) + 1

    def add(
        self,
        urun_kodu: str,
        hedef_fiyat: float,
        yon: str = "yukari"
    ) -> Optional[Dict]:
        """
        Yeni alarm ekle

        Args:
            urun_kodu: Ürün kodu (örn: "AJDA_10GR", "CEYREKALTIN")
            hedef_fiyat: Hedef fiyat (TL)
            yon: "yukari" veya "asagi"

        Returns:
            Eklenen alarm veya None
        """
        if urun_kodu not in TUM_URUNLER:
            return None

        urun = TUM_URUNLER[urun_kodu]
        alarms = self._load()

        yeni_alarm = {
            "id": self._generate_id(alarms),
            "urun_kodu": urun_kodu,
            "urun_adi": urun["ad"],
            "emoji": urun["emoji"],
            "hedef_fiyat": hedef_fiyat,
            "yon": yon,
            "aktif": True,
            "tetiklendi": False,
            "son_bildirim_fiyat": None,
            "olusturma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        alarms.append(yeni_alarm)
        self._save(alarms)

        return yeni_alarm

    def delete(self, alarm_id: int) -> bool:
        """Alarm sil"""
        alarms = self._load()
        initial_count = len(alarms)

        alarms = [a for a in alarms if a["id"] != alarm_id]

        if len(alarms) < initial_count:
            self._save(alarms)
            return True

        return False

    def get_all(self, only_active: bool = False) -> List[Dict]:
        """Tüm alarmları getir"""
        alarms = self._load()

        if only_active:
            return [a for a in alarms if a["aktif"]]

        return alarms

    def get_by_id(self, alarm_id: int) -> Optional[Dict]:
        """ID ile alarm getir"""
        alarms = self._load()

        for alarm in alarms:
            if alarm["id"] == alarm_id:
                return alarm

        return None

    def toggle(self, alarm_id: int) -> Optional[Dict]:
        """Alarmı aç/kapat"""
        alarms = self._load()

        for alarm in alarms:
            if alarm["id"] == alarm_id:
                alarm["aktif"] = not alarm["aktif"]
                self._save(alarms)
                return alarm

        return None

    def update_trigger_state(
        self,
        alarm_id: int,
        tetiklendi: bool,
        son_fiyat: float
    ):
        """Alarm tetiklenme durumunu güncelle"""
        alarms = self._load()

        for alarm in alarms:
            if alarm["id"] == alarm_id:
                alarm["tetiklendi"] = tetiklendi
                alarm["son_bildirim_fiyat"] = son_fiyat
                self._save(alarms)
                return

    def check_alarms(
        self,
        gold_service: GoldAPIService,
        data: Dict
    ) -> List[Dict]:
        """
        Tüm alarmları kontrol et ve tetiklenenleri döndür

        Returns:
            Tetiklenen alarm bildirimleri listesi
        """
        notifications = []
        alarms = self._load()
        changed = False

        for alarm in alarms:
            if not alarm["aktif"]:
                continue

            guncel_fiyat = gold_service.get_price(alarm["urun_kodu"], data)

            if guncel_fiyat is None:
                continue

            hedef = alarm["hedef_fiyat"]
            yon = alarm["yon"]

            # İlk tetikleme kontrolü
            if not alarm["tetiklendi"]:
                tetiklendi = False

                if yon == "yukari" and guncel_fiyat >= hedef:
                    tetiklendi = True
                elif yon == "asagi" and guncel_fiyat <= hedef:
                    tetiklendi = True

                if tetiklendi:
                    alarm["tetiklendi"] = True
                    alarm["son_bildirim_fiyat"] = guncel_fiyat
                    changed = True

                    notifications.append({
                        "type": "trigger",
                        "alarm": alarm.copy(),
                        "guncel_fiyat": guncel_fiyat
                    })

            # Takip bildirimi (her BILDIRIM_ESIK TL değişimde)
            else:
                son_fiyat = alarm.get("son_bildirim_fiyat") or hedef
                fark = guncel_fiyat - son_fiyat

                bildir = False

                if yon == "yukari" and fark >= BILDIRIM_ESIK:
                    bildir = True
                elif yon == "asagi" and fark <= -BILDIRIM_ESIK:
                    bildir = True

                if bildir:
                    alarm["son_bildirim_fiyat"] = guncel_fiyat
                    changed = True

                    notifications.append({
                        "type": "follow",
                        "alarm": alarm.copy(),
                        "guncel_fiyat": guncel_fiyat,
                        "fark": fark
                    })

        if changed:
            self._save(alarms)

        return notifications


# ============================================================
#                    SERVİS INSTANCE'LARI
# ============================================================

gold_service = GoldAPIService()
alarm_service = AlarmService()