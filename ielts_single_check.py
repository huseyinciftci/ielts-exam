#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions için tek seferlik IELTS tarih kontrolü
"""

import os
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Türkiye timezone
TURKEY_TZ = timezone(timedelta(hours=3))

def get_turkey_time():
    """Türkiye saatini döndürür"""
    return datetime.now(TURKEY_TZ)

# GitHub Actions environment variables'tan config al
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
BASE_URL = os.getenv('BASE_URL', 'https://ielts.idp.com/book/IELTS')
COUNTRY_ID = os.getenv('COUNTRY_ID', '212')
LOCATION = os.getenv('LOCATION', 'Ankara')
TEST_TYPE = os.getenv('TEST_TYPE', 'Academic - IELTS')

# TARGET_MONTHS için güvenli parsing
target_months_str = os.getenv('TARGET_MONTHS', '7,8')
if target_months_str and target_months_str.strip():
    TARGET_MONTHS = [int(x.strip()) for x in target_months_str.split(',') if x.strip()]
else:
    TARGET_MONTHS = [7, 8]  # Default: Temmuz ve Ağustos

TARGET_YEAR = int(os.getenv('TARGET_YEAR', '2025'))
HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'
IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', '10'))
ENABLE_POSITIVE_NOTIFICATIONS = os.getenv('ENABLE_POSITIVE_NOTIFICATIONS', 'True').lower() == 'true'
ENABLE_NEGATIVE_NOTIFICATIONS = os.getenv('ENABLE_NEGATIVE_NOTIFICATIONS', 'True').lower() == 'true'

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IELTSChecker:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Chrome WebDriver'ı yapılandırır"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(IMPLICIT_WAIT)
            
            # Automation detection'ı bypass et
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Chrome WebDriver başarıyla başlatıldı")
            return True
        except Exception as e:
            logger.error(f"❌ WebDriver başlatma hatası: {e}")
            return False
    
    def send_telegram_message(self, message):
        """Telegram'a mesaj gönderir"""
        if not CHAT_ID:
            logger.warning("⚠️ CHAT_ID tanımlanmamış, mesaj gönderilemiyor")
            return False
            
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            if result["ok"]:
                logger.info("✅ Telegram mesajı gönderildi")
                return True
            else:
                logger.error(f"❌ Telegram mesaj hatası: {result}")
                return False
        except Exception as e:
            logger.error(f"❌ Telegram gönderme hatası: {e}")
            return False
    
    def fill_registration_form(self):
        """Kayıt formunu doldurur"""
        try:
            # Ana sayfaya git
            self.driver.get(BASE_URL)
            logger.info("📋 Kayıt formuna gidildi")
            
            # Sayfanın yüklenmesini bekle
            time.sleep(3)
            
            # Ülke seçimi
            country_select = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "CountryId"))
            )
            Select(country_select).select_by_value(COUNTRY_ID)
            logger.info(f"🌍 Ülke seçildi: Turkey")
            
            time.sleep(3)
            
            # Lokasyon seçimi
            location_select = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "TestCentreLocationName"))
            )
            Select(location_select).select_by_visible_text(LOCATION)
            logger.info(f"📍 Lokasyon seçildi: {LOCATION}")
            
            time.sleep(3)
            
            # Test türü seçimi
            test_type_select = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "TestModuleId"))
            )
            Select(test_type_select).select_by_visible_text(TEST_TYPE)
            logger.info(f"📝 Test türü seçildi: {TEST_TYPE}")
            
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Form doldurma hatası: {e}")
            return False
    
    def check_available_dates(self):
        """Bilkent University için müsait tarihleri kontrol eder"""
        try:
            available_dates = []
            
            # Venue bölümünü bekle
            venue_section = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "venue-selection-results"))
            )
            logger.info("🏢 Venue bölümü bulundu")
            
            # Bilkent University linkini bul
            bilkent_selectors = [
                (By.XPATH, "//a[@data-target='#venue-info-1771']"),
                (By.XPATH, "//a[contains(text(), 'Bilkent University')]"),
                (By.XPATH, "//a[contains(@data-target, 'venue-info-1771')]"),
                (By.PARTIAL_LINK_TEXT, "Bilkent University")
            ]
            
            bilkent_link = None
            for selector_type, selector_value in bilkent_selectors:
                try:
                    bilkent_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    logger.info(f"🏢 Bilkent University linki bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
                    
            if not bilkent_link:
                logger.warning("⚠️ Bilkent University linki bulunamadı")
                return []
            
            # Bilkent University'ye tıkla
            bilkent_link.click()
            time.sleep(5)
            logger.info("✅ Bilkent University açıldı")
            
            # Datepicker'ı bekle
            datepicker = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "session-date-1771"))
            )
            logger.info("📅 Datepicker bulundu")
            time.sleep(3)
            
            # Müsait tarihleri ara
            date_selectors = [
                (By.CSS_SELECTOR, "td.high-availability-date a"),
                (By.CSS_SELECTOR, "td.medium-availability-date a"),
                (By.CSS_SELECTOR, "td[data-handler='selectDay']:not(.ui-datepicker-unselectable) a"),
                (By.CSS_SELECTOR, "td:not(.ui-datepicker-unselectable):not(.ui-state-disabled) a")
            ]
            
            available_date_elements = []
            for selector_type, selector_value in date_selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if elements:
                        logger.info(f"📅 {len(elements)} tarih elementi bulundu: {selector_value}")
                        available_date_elements = elements
                        break
                except Exception:
                    continue
            
            if not available_date_elements:
                logger.info("📅 Bilkent University için müsait tarih bulunamadı")
                return []
            
            # Tarihleri parse et
            for date_elem in available_date_elements:
                try:
                    parent_td = date_elem.find_element(By.XPATH, "..")
                    data_month = parent_td.get_attribute("data-month")
                    data_year = parent_td.get_attribute("data-year")
                    date_text = date_elem.text.strip()
                    
                    if data_month and data_year and date_text:
                        try:
                            month = int(data_month) + 1  # 0-based to 1-based
                            year = int(data_year)
                            day = int(date_text)
                            
                            date_obj = datetime(year, month, day)
                            
                            if (date_obj.month in TARGET_MONTHS and 
                                date_obj.year == TARGET_YEAR):
                                
                                available_dates.append({
                                    "date": date_obj,
                                    "venue": "Bilkent University",
                                    "date_str": date_obj.strftime("%Y-%m-%d")
                                })
                                
                                logger.info(f"✅ Hedef tarih bulundu: {date_obj.strftime('%d %B %Y')} - Bilkent University")
                        
                        except (ValueError, TypeError) as parse_error:
                            logger.debug(f"📅 Tarih parse hatası: {date_text}, {data_month}, {data_year}")
                            continue
                
                except Exception as elem_error:
                    logger.debug(f"📅 Element okuma hatası: {elem_error}")
                    continue
            
            return available_dates
            
        except Exception as e:
            logger.error(f"❌ Tarih kontrol hatası: {e}")
            return []
    
    def format_dates_message(self, dates):
        """Tarih listesini mesaj formatına çevirir"""
        turkey_time = get_turkey_time()
        
        if not dates:
            return f"❌ Temmuz-Ağustos aylarında Bilkent University'de müsait IELTS tarihi bulunamadı.\n⏰ Kontrol: {turkey_time.strftime('%H:%M:%S')}"
        
        message = "🎉 <b>YENİ IELTS TARİHLERİ BULUNDU!</b>\n\n"
        message += f"📍 <b>Bilkent University</b>\n"
        
        sorted_dates = sorted([d["date"] for d in dates])
        for date in sorted_dates:
            message += f"   📅 {date.strftime('%d %B %Y - %A')}\n"
        
        message += f"\n🔗 <a href='{BASE_URL}'>Hemen Kayıt Ol</a>\n"
        message += f"⏰ GitHub Actions Kontrolü: {turkey_time.strftime('%H:%M:%S')}"
        
        return message
    
    def should_send_negative_notification(self):
        """2 saatte bir başarısız mesaj gönderilip gönderilmeyeceğini kontrol eder"""
        turkey_time = get_turkey_time()
        
        # Her saat 0 ve 30. dakikalarda negatif mesaj gönder (2 saatte bir)
        # 10 dakikalık interval ile çalışırken bu saatlerde mesaj gönder
        current_minute = turkey_time.minute
        current_hour = turkey_time.hour
        
        # 2 saatte bir: çift saatlerde saat başında (00:00, 02:00, 04:00, ...)
        # veya saat 30'da (00:30, 02:30, 04:30, ...)
        if current_hour % 2 == 0 and current_minute < 10:  # İlk 10 dakikada
            return True
        return False
    
    def run_single_check(self):
        """Tek seferlik kontrol yapar"""
        try:
            logger.info("🔄 GitHub Actions IELTS tarih kontrolü başlatılıyor...")
            
            if not self.setup_driver():
                return False
            
            if not self.fill_registration_form():
                return False
            
            available_dates = self.check_available_dates()
            
            if available_dates and ENABLE_POSITIVE_NOTIFICATIONS:
                # Pozitif sonuç - hemen mesaj gönder
                message = self.format_dates_message(available_dates)
                self.send_telegram_message(message)
            elif not available_dates and ENABLE_NEGATIVE_NOTIFICATIONS:
                # Negatif sonuç - sadece 2 saatte bir gönder
                if self.should_send_negative_notification():
                    message = self.format_dates_message([])
                    self.send_telegram_message(message)
                    logger.info("📱 2 saatlik interval - negatif mesaj gönderildi")
                else:
                    logger.info("⏰ 2 saatlik interval - negatif mesaj bekleniyor")
            
            logger.info(f"✅ GitHub Actions kontrolü tamamlandı. {len(available_dates)} tarih bulundu.")
            return True
            
        except Exception as e:
            logger.error(f"❌ GitHub Actions genel hatası: {e}")
            error_message = f"⚠️ GitHub Actions IELTS Bot Hatası\n\n❌ {str(e)}\n⏰ {get_turkey_time().strftime('%H:%M:%S')}"
            self.send_telegram_message(error_message)
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Ana fonksiyon"""
    checker = IELTSChecker()
    success = checker.run_single_check()
    
    if success:
        logger.info("🎉 GitHub Actions başarıyla tamamlandı!")
    else:
        logger.error("❌ GitHub Actions hatası!")
        exit(1)

if __name__ == "__main__":
    main() 