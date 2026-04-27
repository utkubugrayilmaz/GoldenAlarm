"""
GoldenAlarm - Servis Katmanı
API bağlantısı ve Alarm yönetimi
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

import requests
import urllib3

from config import (
    API_URL,
    API_TIMEOUT,
    ALARMS_FILE,
    ALTIN_TURLERI,
    OZEL_URUNLER,
    TUM_URUNLER,
    BILDIRIM_ESIK
)

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
#                      API SERVİSİ
# ============================================================

class GoldAPIService:
    """Altın fiyatları API servisi"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Connection": "keep-alive",
        })
        self.session.verify = False  # SSL kontrolünü kapat
        self.last_data: Optional[Dict] = None
        self.last_update: Optional[datetime] = None

    def fetch_prices(self) -> Dict[str, Any]:
        """API'den güncel fiyatları çek"""
        try:
            response = self.session.get(API_URL, timeout=API_TIMEOUT)
            response.raise_for_status()

            self.last_data = response.json()
            self.last_update = datetime.now()

            return {"success": True, "data": self.last_data}

        except requests.exceptions.RequestException as e:
            # Bağlantı hatası olursa session'ı yenile
            self._reset_session()
            return {"success": False, "error": f"Bağlantı hatası: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"JSON parse hatası: {str(e)}"}

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
                return float(data[kaynak].get("Buying", 0)) * carpan
            return None

        # Normal altın
        if urun_kodu in data:
            return float(data[urun_kodu].get("Buying", 0))

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