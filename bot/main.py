import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
    ConversationHandler
)

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL  = os.getenv("BASE_URL", "http://localhost:3000")

print(f"📄 .env exists  : {ENV_PATH.exists()}")
print(f"🔑 Token loaded : {'YES ✅' if BOT_TOKEN else 'NO ❌'}")
print(f"☁️  Cloudinary  : {os.getenv('CLOUDINARY_CLOUD_NAME') or 'NOT SET ❌'}")

if not BOT_TOKEN:
    print("❌ No token found!")
    sys.exit(1)

PLATFORM, LINK, QUALITY = range(3)
FEEDBACK_STATE = 99

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

QUALITY_LABELS = {
    "1080":  "1080p Full HD 🎥",
    "720":   "720p HD 📺",
    "480":   "480p Medium 📱",
    "360":   "360p Low 📉",
    "audio": "Audio Only MP3 🔉"
}


# ─── DOWNLOAD FLOW ───────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"✅ /start from {update.effective_user.first_name}")
    keyboard = [
        [InlineKeyboardButton("🎬 YouTube",   callback_data="youtube"),
         InlineKeyboardButton("📘 Facebook",  callback_data="facebook")],
        [InlineKeyboardButton("📸 Instagram", callback_data="instagram"),
         InlineKeyboardButton("🎵 TikTok",    callback_data="tiktok")],
        [InlineKeyboardButton("🐦 Twitter/X", callback_data="twitter"),
         InlineKeyboardButton("🔗 Other URL", callback_data="other")],
    ]
    await update.message.reply_text(
        f"👋 Hello *{update.effective_user.first_name}*! Welcome to *Video Downloader Bot*\n\n"
        f"📥 Download from YouTube, Instagram, TikTok & 1000+ sites!\n\n"
        f"👇 *Choose a platform:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PLATFORM


async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    platform = query.data
    context.user_data["platform"] = platform

    examples = {
        "youtube":   "https://youtube.com/watch?v=xxxxx",
        "facebook":  "https://facebook.com/video/xxxxx",
        "instagram": "https://instagram.com/reel/xxxxx",
        "tiktok":    "https://tiktok.com/@user/video/xxxxx",
        "twitter":   "https://twitter.com/user/status/xxxxx",
        "other":     "https://example.com/video.mp4",
    }
    names = {
        "youtube": "YouTube 🎬", "facebook": "Facebook 📘",
        "instagram": "Instagram 📸", "tiktok": "TikTok 🎵",
        "twitter": "Twitter/X 🐦", "other": "Direct URL 🔗",
    }
    await query.edit_message_text(
        f"✅ Platform: *{names.get(platform)}*\n\n"
        f"🔗 *Paste your video link below:*\n\n"
        f"📌 Example:\n`{examples.get(platform)}`\n\n"
        f"❌ Cancel: /cancel",
        parse_mode="Markdown"
    )
    return LINK


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text(
            "❌ Invalid link! Please paste a proper URL.\nTry again 👇"
        )
        return LINK
    context.user_data["url"] = url
    keyboard = [
        [InlineKeyboardButton("🎥 1080p", callback_data="1080"),
         InlineKeyboardButton("📺 720p",  callback_data="720")],
        [InlineKeyboardButton("📱 480p",  callback_data="480"),
         InlineKeyboardButton("📉 360p",  callback_data="360")],
        [InlineKeyboardButton("🔉 Audio Only (MP3)", callback_data="audio")],
    ]
    await update.message.reply_text(
        f"✅ *Link received!*\n\n`{url[:60]}`\n\n🎬 *Choose quality:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return QUALITY


async def quality_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    quality  = query.data
    url      = context.user_data.get("url")
    platform = context.user_data.get("platform", "other")
    label    = QUALITY_LABELS.get(quality, quality)
    user_id  = str(update.effective_user.id)

    await query.edit_message_text(
        f"⏳ *Downloading...*\n\n"
        f"🔗 `{url[:50]}...`\n"
        f"🎬 {label}\n\n"
        f"Please wait 30–60 sec ⏳",
        parse_mode="Markdown"
    )

    from utils.downloader import download_video
    from utils.cloudinary_upload import upload_to_cloudinary
    import asyncio
    import requests as req

    try:
        # Step 1 — Download video with yt-dlp
        loop = asyncio.get_event_loop()
        file_path, file_name, file_size = await loop.run_in_executor(
            None, download_video, url, quality
        )
        size_mb = round(file_size / (1024 * 1024), 2)

        # Update message — show upload progress
        await query.edit_message_text(
            f"✅ *Downloaded! Now uploading...*\n\n"
            f"📁 `{file_name}`\n"
            f"📦 {size_mb} MB\n\n"
            f"☁️ Uploading to cloud... please wait ⏳",
            parse_mode="Markdown"
        )

        MAX_TG = 50 * 1024 * 1024  # 50 MB

        if file_size <= MAX_TG:
            # ✅ Small file — send directly in Telegram chat
            with open(file_path, "rb") as vf:
                await query.message.reply_video(
                    video=vf,
                    caption=(
                        f"📁 {file_name}\n"
                        f"📦 {size_mb} MB  |  🎬 {label}\n\n"
                        f"💾 Tap & hold → Save  |  3 dots → Download\n"
                        f"🤖 @Mylocalvideo_bot"
                    ),
                    supports_streaming=True,
                    read_timeout=180,
                    write_timeout=180,
                    connect_timeout=60,
                )
            await query.edit_message_text(
                f"✅ *Video sent below!*\n\n"
                f"📁 `{file_name}`\n"
                f"📦 {size_mb} MB | 🎬 {label}\n\n"
                f"👇 Tap & hold (mobile) or 3 dots (PC) to save\n"
                f"🔄 New download: /start",
                parse_mode="Markdown"
            )
            # Delete local file
            if os.path.exists(file_path):
                os.remove(file_path)

        else:
            # ❌ Large file — upload to Cloudinary
            cloudinary_url = await loop.run_in_executor(
                None, upload_to_cloudinary, file_path, file_name
            )

            await query.edit_message_text(
                f"✅ *Download Ready!*\n\n"
                f"📁 `{file_name}`\n"
                f"📦 {size_mb} MB\n"
                f"🎬 {label}\n\n"
                f"👇 *Click to download:*\n"
                f"[⬇️ Download Now]({cloudinary_url})\n\n"
                f"🔄 New download: /start",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

        # Save to history
        try:
            req.post(f"{BASE_URL}/api/history", json={
                "userId":   user_id,
                "fileName": file_name,
                "platform": platform,
                "quality":  quality,
                "sizeMb":   size_mb,
                "url":      url,
            }, timeout=5)
        except Exception:
            pass

    except Exception as e:
        print(f"❌ Error: {e}")
        await query.edit_message_text(
            f"❌ *Download failed!*\n\n"
            f"Reason: {str(e)[:150]}\n\n"
            f"🔄 Try again: /start",
            parse_mode="Markdown"
        )

    context.user_data.clear()
    return ConversationHandler.END


# ─── ALL OTHER COMMANDS ──────────────────────────────────

from handlers.commands import (
    help_cmd, about_cmd, status_cmd,
    history_cmd, clear_cmd, clear_callback,
    stats_cmd, feedback_cmd, receive_feedback,
    cancel_cmd, FEEDBACK_STATE
)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ *Cancelled!*\n\nType /start to begin again.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ─── MAIN ────────────────────────────────────────────────

def main():
    print("\n🤖 Starting Telegram Downloader Bot...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Feedback conversation
    feedback_conv = ConversationHandler(
        entry_points=[CommandHandler("feedback", feedback_cmd)],
        states={
            FEEDBACK_STATE: [MessageHandler(
                filters.TEXT & ~filters.COMMAND, receive_feedback
            )],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
    )

    # Main download conversation
    download_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PLATFORM: [CallbackQueryHandler(platform_selected)],
            LINK:     [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            QUALITY:  [CallbackQueryHandler(quality_selected)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
        allow_reentry=True,
    )

    # Register all handlers
    app.add_handler(download_conv)
    app.add_handler(feedback_conv)
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CommandHandler("about",   about_cmd))
    app.add_handler(CommandHandler("status",  status_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("clear",   clear_cmd))
    app.add_handler(CommandHandler("stats",   stats_cmd))
    app.add_handler(CallbackQueryHandler(clear_callback, pattern="^clear_"))

    print("✅ All commands registered!")
    print("💬 Send /start to your bot in Telegram")
    print("🛑 Press Ctrl+C to stop\n")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()