#!/bin/bash

echo "🎯 IELTS Takip Botu Kurulum Scripti"
echo "=================================="

# Python sürümünü kontrol et
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✅ Python kurulu: $python_version"
else
    echo "❌ Python 3 kurulu değil. Lütfen Python 3.8+ kurun."
    exit 1
fi

# pip kurulu mu kontrol et
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 kurulu"
else
    echo "❌ pip3 kurulu değil"
    exit 1
fi

# Chrome kurulu mu kontrol et
if command -v google-chrome &> /dev/null; then
    chrome_version=$(google-chrome --version)
    echo "✅ Chrome kurulu: $chrome_version"
elif command -v chromium &> /dev/null; then
    chromium_version=$(chromium --version)
    echo "✅ Chromium kurulu: $chromium_version"
elif command -v chromium-browser &> /dev/null; then
    chromium_version=$(chromium-browser --version)
    echo "✅ Chromium kurulu: $chromium_version"
else
    echo "⚠️  Chrome/Chromium bulunamadı. Selenium için gerekli olabilir."
    echo "   macOS: brew install --cask google-chrome"
    echo "   Ubuntu: sudo apt install chromium-browser"
fi

echo ""
echo "📦 Python paketleri kuruluyor..."

# Virtual environment oluştur (opsiyonel)
read -p "🤔 Virtual environment oluşturmak ister misiniz? (y/n): " create_venv
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "📁 Virtual environment oluşturuluyor..."
    python3 -m venv ielts_bot_env
    source ielts_bot_env/bin/activate
    echo "✅ Virtual environment aktif"
fi

# Paketleri kur
pip3 install -r requirements.txt

if [[ $? -eq 0 ]]; then
    echo "✅ Tüm paketler başarıyla kuruldu"
else
    echo "❌ Paket kurulumunda hata oluştu"
    exit 1
fi

echo ""
echo "🎉 Kurulum tamamlandı!"
echo ""
echo "📋 Sıradaki adımlar:"
echo "1. Telegram'da @BotFather'dan bot oluşturun"
echo "2. python telegram_test.py ile test edin"
echo "3. config.py dosyasında CHAT_ID güncelleyin"
echo "4. python ielts_tracker.py ile botu başlatın"
echo ""
echo "📖 Detaylı talimatlar için README.md dosyasını okuyun" 