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

if name == "main":
    main()