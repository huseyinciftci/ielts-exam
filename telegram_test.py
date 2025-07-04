#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from config import TELEGRAM_BOT_TOKEN

def get_chat_id():
    """Telegram bot updates'ini kontrol ederek Chat ID'yi bulur"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["ok"] and data["result"]:
            # En son mesajdan chat ID'yi al
            chat_id = data["result"][-1]["message"]["chat"]["id"]
            print(f"Chat ID bulundu: {chat_id}")
            return chat_id
        else:
            print("Henüz bot'a mesaj gönderilmemiş. Lütfen bot'a /start mesajı gönderin.")
            return None
    except Exception as e:
        print(f"Chat ID alınırken hata: {e}")
        return None

def send_test_message(chat_id, message):
    """Test mesajı gönderir"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        if result["ok"]:
            print("✅ Test mesajı başarıyla gönderildi!")
            return True
        else:
            print(f"❌ Mesaj gönderilemedi: {result}")
            return False
    except Exception as e:
        print(f"❌ Mesaj gönderme hatası: {e}")
        return False

if __name__ == "__main__":
    print("🤖 IELTS Takip Botu - Telegram Test")
    print("=" * 40)
    
    # Chat ID'yi bul
    chat_id = get_chat_id()
    
    if chat_id:
        # Test mesajı gönder
        test_message = """
🧪 <b>IELTS Takip Botu Test Mesajı</b>

✅ Bot başarıyla çalışıyor!
📊 Chat ID: <code>{}</code>

Bu mesajı aldıysanız bot kurulumu tamamdır.
        """.format(chat_id)
        
        send_test_message(chat_id, test_message)
        
        # Config dosyasını güncelle
        print(f"\n📝 Chat ID'yi config.py dosyasında güncelleyin:")
        print(f"CHAT_ID = {chat_id}")
    else:
        print("\n📱 Lütfen önce Telegram'da bot'unuza /start mesajı gönderin.")
        print(f"Bot linki: https://t.me/MacBerKBot") 