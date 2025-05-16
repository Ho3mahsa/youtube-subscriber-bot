import requests
import asyncio
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import pytz

TELEGRAM_BOT_TOKEN = "7638829484:AAGyNgYBona3wFjlvzINKRrI0t7j5nkiA7g"
YOUTUBE_API_KEY = "AIzaSyCsLenrm7vyzZcyYslZDT7Loi2i7I42mpU"
CHANNEL_ID = "UC_4KhTXkLoVHHoWRBz-SAbw"
MILESTONES = [45000, 50000, 55000]

active_users = set()
is_running = False
notified_milestones = set()
last_report_time = None

def get_subscriber_count():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return int(data["items"][0]["statistics"]["subscriberCount"])
    except Exception as e:
        print(f"خطا در دریافت آمار: {e}")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running, active_users, last_report_time
    user_id = update.effective_user.id
    active_users.add(user_id)

    if not is_running:
        is_running = True
        last_report_time = datetime.now(pytz.timezone('Asia/Tehran'))
        context.job_queue.run_repeating(check_subscribers, interval=60, first=10)
        context.job_queue.run_repeating(send_subscriber_report, interval=10800, first=10800)

    subs = get_subscriber_count()
    status = f"تعداد فعلی مشترکین: {subs:,}" if subs else "نامشخص"
    next_report = (last_report_time + timedelta(hours=3)).strftime("%Y/%m/%d %H:%M")

    await update.message.reply_text(
        f"✅ ربات فعال شد!\n\n"
        f"📊 وضعیت فعلی:\n"
        f"👥 {status}\n"
        f"👤 تعداد کاربران فعال: {len(active_users)}\n"
        f"⏰ گزارش بعدی در ساعت {next_report}\n\n"
        f"🎯 اعلان در مایلستون‌های: {', '.join(f'{m:,}' for m in MILESTONES)}"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running, active_users
    user_id = update.effective_user.id
    active_users.discard(user_id)

    await update.message.reply_text(
        "⏹ شما از لیست دریافت اعلان‌ها خارج شدید.\n"
        "برای دریافت مجدد از /start استفاده کنید."
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = get_subscriber_count()
    global last_report_time
    
    if last_report_time is None:
        last_report_time = datetime.now(pytz.timezone('Asia/Tehran'))
    
    next_report = (last_report_time + timedelta(hours=3)).strftime("%Y/%m/%d %H:%M")

    if subs:
        next_milestone = next((m for m in MILESTONES if m > subs), None)
        milestone_msg = f"\n⭐️ تا مایلستون بعدی ({next_milestone:,}): {next_milestone - subs:,} مشترک" if next_milestone else "\n🎉 تمام مایلستون‌ها پشت سر گذاشته شدند!"

        await update.message.reply_text(
            f"📊 آمار کانال:\n"
            f"👥 تعداد مشترکین: {subs:,}\n"
            f"👤 کاربران فعال: {len(active_users)}\n"
            f"⚡️ وضعیت ربات: {'🟢 فعال' if is_running else '🔴 غیرفعال'}\n"
            f"⏰ گزارش بعدی: {next_report}"
            f"{milestone_msg}"
        )
    else:
        await update.message.reply_text("❌ خطا در دریافت آمار")

async def send_subscriber_report(context: ContextTypes.DEFAULT_TYPE):
    global last_report_time
    if not is_running or not active_users:
        return

    last_report_time = datetime.now(pytz.timezone('Asia/Tehran'))
    next_report = (last_report_time + timedelta(hours=3)).strftime("%Y/%m/%d %H:%M")
    subs = get_subscriber_count()

    if subs:
        report = (
            f"📊 گزارش دوره‌ای\n"
            f"👥 تعداد مشترکین: {subs:,}\n"
            f"⏰ گزارش بعدی در ساعت {next_report}"
        )
        for user_id in active_users:
            try:
                await context.bot.send_message(chat_id=user_id, text=report)
            except Exception as e:
                print(f"خطا در ارسال پیام به کاربر {user_id}: {e}")

async def check_subscribers(context: ContextTypes.DEFAULT_TYPE):
    global notified_milestones
    if not is_running or not active_users:
        return

    subs = get_subscriber_count()
    if subs:
        for milestone in MILESTONES:
            if subs >= milestone and milestone not in notified_milestones:
                message = f"🎉 تبریک!\n👥 تعداد مشترکین کانال به {milestone:,} رسید!"
                notified_milestones.add(milestone)
                for user_id in active_users:
                    try:
                        await context.bot.send_message(chat_id=user_id, text=message)
                    except Exception as e:
                        print(f"خطا در ارسال پیام به کاربر {user_id}: {e}")

def main():
    try:
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stop", stop))
        app.add_handler(CommandHandler("stats", stats))

        print("ربات در حال اجرا...")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        print(f"خطای اصلی: {e}")
        # در صورت خطا، 5 ثانیه صبر کرده و دوباره تلاش می‌کند
        import time
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()