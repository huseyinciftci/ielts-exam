# 🎯 IELTS Takip Botu

Bilkent Üniversitesi öğrencileri için IELTS sınav tarihlerini otomatik takip eden Telegram botu.

## 🚀 Özellikler

- ✅ Otomatik IELTS tarih kontrolü
- 📱 Telegram bildirim sistemi
- 🎯 Ankara lokasyonu ve Academic IELTS odaklı
- ⏰ 30 dakikada bir periyodik kontrol
- 📊 Detaylı logging sistemi
- 🔐 Otomatik giriş yapma

## 📋 Gereksinimler

- Python 3.8+
- Chrome/Chromium tarayıcısı
- Telegram Bot Token
- IELTS.IDP hesabı

## ⚙️ Kurulum

### 1. Proje Kurulumu
```bash
# Gerekli paketleri kur
pip install -r requirements.txt
```

### 2. Telegram Bot Oluşturma
1. Telegram'da @BotFather'ı bulun
2. `/newbot` komutunu gönderin
3. Bot adı ve kullanıcı adı belirleyin
4. Verilen token'ı kaydedin

### 3. Chat ID Bulma
```bash
# Test scriptini çalıştır
python telegram_test.py
```
1. Önce bot'unuza `/start` mesajı gönderin
2. Script size Chat ID'nizi verecek
3. Bu ID'yi `config.py` dosyasında güncelleyin

### 4. Konfigürasyon
`config.py` dosyasında `CHAT_ID` değerini güncelleyin:
```python
CHAT_ID = 123456789  # telegram_test.py'den aldığınız ID
```

## 🔧 Kullanım

### Test Çalıştırma
```bash
# Telegram bağlantısını test et
python telegram_test.py

# Tek seferlik IELTS kontrolü
python ielts_tracker.py
```

### Sürekli Çalıştırma
```bash
# Bot'u başlat (30dk'da bir kontrol eder)
python ielts_tracker.py
```

### Arka Planda Çalıştırma (macOS/Linux)
```bash
# Arka planda çalıştır
nohup python ielts_tracker.py > bot.log 2>&1 &

# Çalışan bot'u kontrol et
ps aux | grep ielts_tracker

# Bot'u durdur
pkill -f ielts_tracker.py
```

## 📊 Loglar

- `ielts_tracker.log`: Detaylı işlem logları
- Konsol çıktısı: Anlık durum bilgileri

## 🔄 Nasıl Çalışır

1. **Giriş**: Belirlenen kullanıcı bilgileri ile IELTS.IDP'ye giriş yapar
2. **Form**: Turkey → Ankara → Academic IELTS seçimlerini yapar  
3. **Kontrol**: Temmuz-Ağustos 2025 aylarında müsait tarihleri arar
4. **Bildirim**: Yeni tarih bulursa/bulamazsa Telegram'dan bildirim gönderir
5. **Tekrar**: 30 dakika sonra tekrar kontrol eder

## ⚠️ Önemli Notlar

- Bot sadece Ankara lokasyonu için Academic IELTS tarihlerini takip eder
- Sadece Temmuz-Ağustos 2025 aylarına odaklanır
- Giriş bilgileri güvenli tutulmalı
- Chrome tarayıcısı kurulu olmalı

## 🛠️ Sorun Giderme

### Chrome Driver Hatası
```bash
# Chrome'un yüklü olduğundan emin olun
google-chrome --version

# Eğer hata alıyorsanız manuel kurulum:
# https://chromedriver.chromium.org/
```

### Selenium Hatalarında
```bash
# Headless mode'u kapatın (config.py)
HEADLESS_MODE = False
```

### Telegram Hatalarında
```bash
# Bot token ve chat ID'yi kontrol edin
python telegram_test.py
```

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. `ielts_tracker.log` dosyasını kontrol edin
2. Telegram test scriptini çalıştırın
3. Gerekli ayarları yeniden kontrol edin

## ⚖️ Yasal Uyarı

Bu bot sadece eğitim amaçlıdır. IELTS.IDP'nin kullanım şartlarına uygun şekilde kullanın. 