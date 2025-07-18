# 🎌 ابزار بهبود یافته مانگا گربر برای تلگرام

ابزاری قدرتمند برای جستجو و دانلود فایل‌های مانگا با فرمت‌های مختلف از کانال‌های تلگرام، همراه با امکانات پیشرفته و رابط‌های کاربری متنوع.

## ✨ امکانات

- **📦 پشتیبانی از چند فرمت**: فایل‌های ZIP، RAR، CBZ
- **🔍 جستجوی هوشمند**: پشتیبانی از هشتگ‌ها (مانند `#نام_مانگا`)
- **⚡ بهینه‌سازی عملکرد**: استفاده از کش و پردازش دسته‌ای
- **📊 قابلیت خروجی گرفتن**: خروجی به فرمت JSON و CSV
- **🖥️ چند رابط کاربری**: خط فرمان، رابط گرافیکی، و ربات تلگرام
- **📈 آمار و گزارشات**: آمار جستجو و تحلیل عملکرد
- **🎯 جستجوی نامحدود**: اسکن کامل تاریخچه کانال
- **🔧 حالت بدون رابط (Headless)**: مناسب برای اجرای خودکار

## 🚀 شروع سریع

### پیش‌نیازها

- پایتون نسخه 3.7 یا بالاتر
- دریافت اطلاعات API تلگرام ([لینک دریافت](https://my.telegram.org/apps))
- نصب بسته‌ها:  
  ```bash
  pip install -r requirements_enhanced.txt
  ```

### نحوه اجرا

1. **نسخه خط فرمان (CLI)**:
   ```bash
   python manga_grabber_enhanced.py
   ```

2. **نسخه گرافیکی (GUI)**:
   ```bash
   python manga_grabber_gui.py
   ```

3. **نسخه ربات تلگرام**:
   ```bash
   python manga_grabber_bot.py
   ```

4. **اجرای خودکار (Headless)**:
   ```bash
   python manga_grabber_enhanced.py --headless --channel @channelname --search "manga title"
   ```

## 📋 نصب

### روش ۱: نصب ساده

```bash
pip install -r requirements.txt
python manga_grabber.py
```

### روش ۲: نصب برای توسعه‌دهندگان

```bash
pip install telethon rarfile python-telegram-bot
pip install tkinter
pip install pandas openpyxl cachetools
```

## 🛠️ پیکربندی

### راه‌اندازی اولیه

۱. دریافت اطلاعات API از [my.telegram.org/apps](https://my.telegram.org/apps)  
۲. اجرای برنامه و وارد کردن اطلاعات  
۳. ذخیره‌سازی اطلاعات برای دفعات بعد

### فایل‌های پیکربندی

- `telegram_config.json`: تنظیمات API تلگرام
- `bot_config.json`: تنظیمات مربوط به ربات

نمونه‌ای از فایل `telegram_config.json`:
```json
{
  "api_id": 12345678,
  "api_hash": "your_api_hash_here",
  "phone_number": "+1234567890"
}
```

