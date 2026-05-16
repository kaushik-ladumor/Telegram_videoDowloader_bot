import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

BASE_URL   = os.getenv("BASE_URL", "http://localhost:3000")
ADMIN_ID   = int(os.getenv("ADMIN_ID", "0"))  # your Telegram user ID


# ─── /help ───────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *How to use Video Downloader Bot:*\n\n"
        "1️⃣ /start → choose platform\n"
        "2️⃣ Paste your video link\n"
        "3️⃣ Choose quality\n"
        "4️⃣ Video appears in chat 🎬\n\n"
        "💾 *To save video:*\n"
        "📱 Mobile → tap & hold → Save\n"
        "💻 PC → click 3 dots → Download\n\n"
        "📋 *All Commands:*\n"
        "/start    - Start a new download\n"
        "/history  - Your last 5 downloads\n"
        "/status   - Check if bot is working\n"
        "/about    - Supported sites & info\n"
        "/feedback - Send feedback to admin\n"
        "/clear    - Clear your history\n"
        "/cancel   - Cancel current action\n"
        "/help     - Show this message",
        parse_mode="Markdown"
    )


# ─── /about ──────────────────────────────────────────────
async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Video Downloader Bot*\n\n"
        "📥 Download videos from 1000+ sites!\n\n"
        "✅ *Supported Platforms:*\n"
        "🎬 YouTube\n"
        "📘 Facebook\n"
        "📸 Instagram (Reels, Posts)\n"
        "🎵 TikTok\n"
        "🐦 Twitter / X\n"
        "🎵 SoundCloud\n"
        "📺 Dailymotion\n"
        "🔗 Any direct video URL\n"
        "...and 1000+ more sites!\n\n"
        "🎬 *Quality Options:*\n"
        "1080p / 720p / 480p / 360p / Audio MP3\n\n"
        "📦 *Limits:*\n"
        "Under 50MB → video sent directly in chat\n"
        "Over 50MB  → download link (10 min expiry)\n\n"
        "🔄 Type /start to download!",
        parse_mode="Markdown"
    )


# ─── /status ─────────────────────────────────────────────
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check Node.js server
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        server_status = "✅ Online" if r.status_code == 200 else "⚠️ Issues"
    except Exception:
        server_status = "❌ Offline"

    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    await update.message.reply_text(
        f"📊 *Bot Status*\n\n"
        f"🤖 Bot:        ✅ Online\n"
        f"🌐 Server:     {server_status}\n"
        f"🕐 Time:       {now}\n"
        f"📥 Downloader: ✅ yt-dlp ready\n\n"
        f"Everything is working! Type /start to download 🚀",
        parse_mode="Markdown"
    )


# ─── /history ────────────────────────────────────────────
async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        r = requests.get(f"{BASE_URL}/api/history/{user_id}", timeout=5)
        data = r.json()

        if not data.get("history") or len(data["history"]) == 0:
            await update.message.reply_text(
                "📭 *No download history yet!*\n\n"
                "Type /start to make your first download.",
                parse_mode="Markdown"
            )
            return

        history = data["history"]
        msg = "📋 *Your Last Downloads:*\n\n"

        for i, item in enumerate(history, 1):
            name     = item.get("fileName", "Unknown")[:35]
            platform = item.get("platform", "unknown").capitalize()
            size     = item.get("sizeMb", "?")
            date     = item.get("date", "")
            msg += f"{i}️⃣ `{name}`\n"
            msg += f"   📌 {platform} | 📦 {size} MB | 🕐 {date}\n\n"

        msg += "🔄 Type /start for a new download!"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(
            "📭 *No history found.*\n\nType /start to make your first download!",
            parse_mode="Markdown"
        )


# ─── /clear ──────────────────────────────────────────────
async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [[
        InlineKeyboardButton("✅ Yes, clear it", callback_data=f"clear_confirm_{user_id}"),
        InlineKeyboardButton("❌ No, keep it",   callback_data="clear_cancel"),
    ]]

    await update.message.reply_text(
        "🗑️ *Clear Download History?*\n\n"
        "This will delete all your download records.\n"
        "Are you sure?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def clear_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "clear_cancel":
        await query.edit_message_text("✅ Cancelled! Your history is safe.")
        return

    user_id = query.data.replace("clear_confirm_", "")

    try:
        r = requests.delete(f"{BASE_URL}/api/history/{user_id}", timeout=5)
        await query.edit_message_text(
            "🗑️ *History cleared successfully!*\n\n"
            "Type /start to make a new download.",
            parse_mode="Markdown"
        )
    except Exception:
        await query.edit_message_text("❌ Failed to clear history. Try again later.")


# ─── /stats (admin only) ─────────────────────────────────
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if ADMIN_ID and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ This command is for admin only!")
        return

    try:
        r = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        data = r.json()

        total      = data.get("totalDownloads", 0)
        today      = data.get("todayDownloads", 0)
        users      = data.get("totalUsers", 0)
        active     = data.get("activeLinks", 0)
        storage_mb = data.get("storageMb", 0)

        await update.message.reply_text(
            f"📊 *Bot Statistics*\n\n"
            f"👥 Total Users:       {users}\n"
            f"📥 Total Downloads:   {total}\n"
            f"📅 Today's Downloads: {today}\n"
            f"🔗 Active Links:      {active}\n"
            f"💾 Storage Used:      {storage_mb} MB\n\n"
            f"🕐 {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Could not fetch stats.\nError: {str(e)[:100]}"
        )


# ─── /feedback ───────────────────────────────────────────
FEEDBACK_STATE = 99

async def feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Send Feedback*\n\n"
        "Type your message below and I'll forward it to the admin.\n\n"
        "❌ To cancel: /cancel",
        parse_mode="Markdown"
    )
    return FEEDBACK_STATE


async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feedback_text = update.message.text
    user = update.effective_user
    user_id = user.id

    # Forward to admin if ADMIN_ID is set
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📬 *New Feedback Received!*\n\n"
                    f"👤 From: {user.first_name} {user.last_name or ''}\n"
                    f"🆔 User ID: `{user_id}`\n"
                    f"📱 Username: @{user.username or 'none'}\n\n"
                    f"💬 *Message:*\n{feedback_text}"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Could not forward feedback: {e}")

    await update.message.reply_text(
        "✅ *Feedback sent! Thank you!*\n\n"
        "The admin will review your message.\n"
        "Type /start to make a new download.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ─── /cancel ─────────────────────────────────────────────
async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ *Cancelled!*\n\nType /start to begin again.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END