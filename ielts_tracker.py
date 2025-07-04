#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import requests
import schedule
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ielts_tracker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IELTSTracker:
    def __init__(self):
        self.driver = None
        self.last_available_dates = set()
        
    def setup_driver(self):
        """Chrome WebDriver'ı yapılandırır"""
        try:
            chrome_options = Options()
            
            # macOS için Chrome binary path
            chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            
            if config.HEADLESS_MODE:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Selenium'un built-in driver manager'ını kullan (Selenium 4.6.0+)
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)
            
            # Automation detection'ı bypass et
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Chrome WebDriver başarıyla başlatıldı")
            return True
        except Exception as e:
            logger.error(f"❌ WebDriver başlatma hatası: {e}")
            return False
    
    def send_telegram_message(self, message):
        """Telegram'a mesaj gönderir"""
        if not config.CHAT_ID:
            logger.warning("⚠️ CHAT_ID tanımlanmamış, mesaj gönderilemiyor")
            return False
            
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": config.CHAT_ID,
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
    
    def login(self):
        """Siteye giriş yapar"""
        try:
            # Ana sayfaya git
            self.driver.get(config.BASE_URL)
            logger.info("📄 Ana sayfaya gidildi")
            
            # Sayfanın yüklenmesini bekle
            time.sleep(3)
            
            # Login linkini farklı selector'larla deneyelim
            login_selectors = [
                (By.LINK_TEXT, "Login Here"),
                (By.PARTIAL_LINK_TEXT, "Login"),
                (By.XPATH, "//a[contains(text(), 'Login')]"),
                (By.CLASS_NAME, "login-link")
            ]
            
            login_link = None
            for selector_type, selector_value in login_selectors:
                try:
                    login_link = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    logger.info(f"🔐 Login linki bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not login_link:
                logger.error("❌ Login linki bulunamadı")
                return False
                
            login_link.click()
            time.sleep(3)
            logger.info("🔐 Login sayfasına gidildi")
            
            # Kullanıcı adı alanını farklı selector'larla deneyelim
            username_selectors = [
                (By.ID, "Username"),
                (By.NAME, "Username"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[contains(@placeholder, 'sername')]")
            ]
            
            username_field = None
            for selector_type, selector_value in username_selectors:
                try:
                    username_field = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"👤 Username alanı bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                logger.error("❌ Username alanı bulunamadı")
                return False
            
            username_field.clear()
            username_field.send_keys(config.USERNAME)
            
            # Şifre alanını farklı selector'larla deneyelim
            password_selectors = [
                (By.ID, "Password"),
                (By.NAME, "Password"),
                (By.XPATH, "//input[@type='password']"),
                (By.XPATH, "//input[contains(@placeholder, 'assword')]")
            ]
            
            password_field = None
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"🔒 Password alanı bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not password_field:
                logger.error("❌ Password alanı bulunamadı")
                return False
                
            password_field.clear()
            password_field.send_keys(config.PASSWORD)
            
            # Login butonunu farklı selector'larla deneyelim
            login_button_selectors = [
                (By.XPATH, "//input[@value='Login']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//input[@type='submit']"),
                (By.CLASS_NAME, "login-button")
            ]
            
            login_button = None
            for selector_type, selector_value in login_button_selectors:
                try:
                    login_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    logger.info(f"🔘 Login butonu bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not login_button:
                logger.error("❌ Login butonu bulunamadı")
                return False
                
            login_button.click()
            time.sleep(5)
            
            # Giriş başarılı mı kontrol et
            success_selectors = [
                (By.PARTIAL_LINK_TEXT, "My Account"),
                (By.PARTIAL_LINK_TEXT, "Account"),
                (By.XPATH, "//a[contains(text(), 'Account')]"),
                (By.CLASS_NAME, "user-menu")
            ]
            
            success = False
            for selector_type, selector_value in success_selectors:
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    success = True
                    logger.info(f"✅ Giriş başarısı onaylandı: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if success:
                logger.info("✅ Başarıyla giriş yapıldı")
                return True
            else:
                logger.error("❌ Giriş başarısı doğrulanamadı")
                return False
            
        except Exception as e:
            logger.error(f"❌ Giriş yapma hatası: {e}")
            return False
    
    def fill_registration_form(self):
        """Kayıt formunu doldurur"""
        try:
            # Kayıt sayfasına git
            self.driver.get(config.BASE_URL)
            logger.info("📋 Kayıt formuna gidildi")
            
            # Sayfanın yüklenmesini bekle
            time.sleep(3)
            
            # Ülke seçimi - farklı selector'larla deneyelim
            country_selectors = [
                (By.ID, "CountryId"),
                (By.NAME, "CountryId"),
                (By.XPATH, "//select[contains(@name, 'Country')]")
            ]
            
            country_select = None
            for selector_type, selector_value in country_selectors:
                try:
                    country_select = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"🌍 Ülke dropdown bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not country_select:
                logger.error("❌ Ülke dropdown bulunamadı")
                return False
                
            Select(country_select).select_by_value(config.COUNTRY_ID)
            logger.info(f"🌍 Ülke seçildi: Turkey")
            
            time.sleep(3)  # Lokasyon dropdown'ının yüklenmesi için bekle
            
            # Lokasyon seçimi - farklı selector'larla deneyelim
            location_selectors = [
                (By.ID, "TestCentreLocationName"),
                (By.NAME, "TestCentreLocationName"),
                (By.XPATH, "//select[contains(@name, 'Location')]")
            ]
            
            location_select = None
            for selector_type, selector_value in location_selectors:
                try:
                    location_select = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"📍 Lokasyon dropdown bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not location_select:
                logger.error("❌ Lokasyon dropdown bulunamadı")
                return False
                
            Select(location_select).select_by_visible_text(config.LOCATION)
            logger.info(f"📍 Lokasyon seçildi: {config.LOCATION}")
            
            time.sleep(3)  # Test türü dropdown'ının yüklenmesi için bekle
            
            # Test türü seçimi - farklı selector'larla deneyelim
            test_type_selectors = [
                (By.ID, "TestModuleId"),
                (By.NAME, "TestModuleId"),
                (By.XPATH, "//select[contains(@name, 'TestModule')]")
            ]
            
            test_type_select = None
            for selector_type, selector_value in test_type_selectors:
                try:
                    test_type_select = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"📝 Test türü dropdown bulundu: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not test_type_select:
                logger.error("❌ Test türü dropdown bulunamadı")
                return False
                
            Select(test_type_select).select_by_visible_text(config.TEST_TYPE)
            logger.info(f"📝 Test türü seçildi: {config.TEST_TYPE}")
            
            time.sleep(5)  # Venue listesinin yüklenmesi için bekle
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Form doldurma hatası: {e}")
            return False
    
    def check_available_dates(self):
        """Müsait tarihleri kontrol eder"""
        try:
            available_dates = []
            
            # Venue seçim bölümünü bekle
            time.sleep(5)
            
            # Venue bölümünü bul
            venue_section = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "venue-selection-results"))
            )
            logger.info("🏢 Venue bölümü bulundu")
            
            # Bilkent University linkini bul
            bilkent_link = None
            try:
                # Farklı selector'larla deneyelim
                bilkent_selectors = [
                    (By.XPATH, "//a[contains(text(), 'Bilkent University')]"),
                    (By.XPATH, "//a[@data-target='#venue-info-1771']"),
                    (By.XPATH, "//a[contains(@data-target, 'venue-info-1771')]"),
                    (By.XPATH, "//h3[@class='panel-title']//a[contains(text(), 'Bilkent')]"),
                    (By.PARTIAL_LINK_TEXT, "Bilkent University"),
                    (By.XPATH, "//div[@class='panel panel-default']//a[normalize-space()='Bilkent University']")
                ]
                
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
                    
            except Exception as e:
                logger.error(f"❌ Bilkent University arama hatası: {e}")
                return []
            
            # Bilkent University'ye tıkla
            try:
                bilkent_link.click()
                time.sleep(5)
                logger.info("✅ Bilkent University açıldı")
            except Exception as click_error:
                logger.error(f"❌ Bilkent University'ye tıklanamadı: {click_error}")
                return []
            
            # Datepicker'ın yüklenmesini bekle
            try:
                datepicker = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "session-date-1771"))
                )
                logger.info("📅 Datepicker bulundu")
                time.sleep(3)  # Takvimin tamamen yüklenmesi için
            except TimeoutException:
                logger.warning("⚠️ Datepicker bulunamadı")
                return []
            
            # Müsait tarihleri bul - farklı stratejilerle
            date_selectors = [
                # 1. High availability dates (yeşil - müsait)
                (By.CSS_SELECTOR, "td.high-availability-date a"),
                (By.CSS_SELECTOR, ".high-availability-date a"),
                # 2. Medium availability dates (sarı - dolmak üzere)  
                (By.CSS_SELECTOR, "td.medium-availability-date a"),
                (By.CSS_SELECTOR, ".medium-availability-date a"),
                # 3. Selected dates (mavi - seçili)
                (By.CSS_SELECTOR, "td.selected-legend a"),
                (By.CSS_SELECTOR, ".selected-legend a"),
                # 4. Genel tıklanabilir tarihler (disabled olmayanlar)
                (By.CSS_SELECTOR, "td[data-handler='selectDay']:not(.ui-datepicker-unselectable) a"),
                # 5. UI datepicker aktif tarihler
                (By.CSS_SELECTOR, "td:not(.ui-datepicker-unselectable):not(.ui-state-disabled) a"),
                # 6. Herhangi bir aktif tarih linki
                (By.XPATH, "//td[@data-handler='selectDay' and not(contains(@class, 'ui-datepicker-unselectable'))]//a"),
                # 7. Tüm tıklanabilir tarih elementleri
                (By.CSS_SELECTOR, "td[data-event='click'] a")
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
                
                # Datepicker içeriğini debug için logla
                try:
                    datepicker_html = datepicker.get_attribute("outerHTML")[:500]
                    logger.debug(f"📅 Datepicker içeriği: {datepicker_html}")
                except:
                    pass
                
                return []
            
            # Tarihleri parse et
            for date_elem in available_date_elements:
                try:
                    # Parent td elementinden tarih bilgilerini al
                    parent_td = date_elem.find_element(By.XPATH, "..")
                    
                    # data-month ve data-year attribute'larını al
                    data_month = parent_td.get_attribute("data-month")
                    data_year = parent_td.get_attribute("data-year")
                    
                    # Tarih metnini al
                    date_text = date_elem.text.strip()
                    
                    if data_month and data_year and date_text:
                        try:
                            # Month 0-based olduğu için +1 ekliyoruz
                            month = int(data_month) + 1
                            year = int(data_year)
                            day = int(date_text)
                            
                            # Date objesi oluştur
                            date_obj = datetime(year, month, day)
                            
                            # Hedef ayları kontrol et
                            if (date_obj.month in config.TARGET_MONTHS and 
                                date_obj.year == config.TARGET_YEAR):
                                
                                available_dates.append({
                                    "date": date_obj,
                                    "venue": "Bilkent University",
                                    "date_str": date_obj.strftime("%Y-%m-%d")
                                })
                                
                                logger.info(f"✅ Hedef tarih bulundu: {date_obj.strftime('%d %B %Y')} - Bilkent University")
                        
                        except (ValueError, TypeError) as parse_error:
                            logger.debug(f"📅 Tarih parse hatası: {date_text}, {data_month}, {data_year} - {parse_error}")
                            continue
                    else:
                        # Alternatif parsing - direkt text'ten
                        full_text = f"{date_text}/{data_month}/{data_year}" if data_month and data_year else date_text
                        logger.debug(f"📅 Alternatif tarih metni: {full_text}")
                
                except Exception as elem_error:
                    logger.debug(f"📅 Element okuma hatası: {elem_error}")
                    continue
            
            return available_dates
            
        except Exception as e:
            logger.error(f"❌ Tarih kontrol hatası: {e}")
            return []
    
    def format_dates_message(self, dates):
        """Tarih listesini mesaj formatına çevirir"""
        if not dates:
            return "❌ Temmuz-Ağustos aylarında müsait IELTS tarihi bulunamadı."
        
        message = "🎉 <b>Yeni IELTS Tarihleri Bulundu!</b>\n\n"
        
        # Tarihleri grupla
        venues = {}
        for date_info in dates:
            venue = date_info["venue"]
            if venue not in venues:
                venues[venue] = []
            venues[venue].append(date_info["date"])
        
        for venue, venue_dates in venues.items():
            message += f"📍 <b>{venue}</b>\n"
            sorted_dates = sorted(venue_dates)
            for date in sorted_dates:
                message += f"   📅 {date.strftime('%d %B %Y - %A')}\n"
            message += "\n"
        
        message += f"🔗 <a href='{config.BASE_URL}'>Hemen Kayıt Ol</a>\n"
        message += f"⏰ Kontrol Zamanı: {datetime.now().strftime('%H:%M:%S')}"
        
        return message
    
    def run_check(self):
        """Tek seferlik kontrol yapar"""
        try:
            logger.info("🔄 IELTS tarih kontrolü başlatılıyor...")
            
            if not self.setup_driver():
                return
            
            # Login adımını atla, direkt form doldur
            if not self.fill_registration_form():
                return
            
            # Tarihleri kontrol et
            available_dates = self.check_available_dates()
            
            # Yeni tarihler var mı kontrol et
            current_dates = {d["date_str"] for d in available_dates}
            new_dates = current_dates - self.last_available_dates
            
            if available_dates and config.ENABLE_POSITIVE_NOTIFICATIONS:
                if new_dates or not self.last_available_dates:  # İlk çalıştırma veya yeni tarih
                    message = self.format_dates_message(available_dates)
                    self.send_telegram_message(message)
            elif not available_dates and config.ENABLE_NEGATIVE_NOTIFICATIONS:
                message = f"❌ Temmuz-Ağustos aylarında müsait IELTS tarihi yok.\n⏰ Kontrol: {datetime.now().strftime('%H:%M:%S')}"
                self.send_telegram_message(message)
            
            # Son durumu kaydet
            self.last_available_dates = current_dates
            
            logger.info(f"✅ Kontrol tamamlandı. {len(available_dates)} tarih bulundu.")
            
        except Exception as e:
            logger.error(f"❌ Genel kontrol hatası: {e}")
            error_message = f"⚠️ IELTS Takip Botu Hatası\n\n❌ {str(e)}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            self.send_telegram_message(error_message)
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

def main():
    """Ana fonksiyon"""
    tracker = IELTSTracker()
    
    logger.info("🚀 IELTS Takip Botu başlatılıyor...")
    
    # İlk kontrol
    tracker.run_check()
    
    # Periyodik kontrol planla
    schedule.every(config.CHECK_INTERVAL_MINUTES).minutes.do(tracker.run_check)
    
    logger.info(f"⏰ Bot {config.CHECK_INTERVAL_MINUTES} dakikada bir kontrol edecek")
    
    # Ana döngü
    while True:
        schedule.run_pending()
        time.sleep(60)  # Her dakika kontrol et

if __name__ == "__main__":
    main() 