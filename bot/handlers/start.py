from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

PLATFORM = 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    keyboard = [
        [
            InlineKeyboardButton("🎬 YouTube",   callback_data="youtube"),
            InlineKeyboardButton("📘 Facebook",  callback_data="facebook"),
        ],
        [
            InlineKeyboardButton("📸 Instagram", callback_data="instagram"),
            InlineKeyboardButton("🎵 TikTok",    callback_data="tiktok"),
        ],
        [
            InlineKeyboardButton("🐦 Twitter/X", callback_data="twitter"),
            InlineKeyboardButton("🔗 Other URL", callback_data="other"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Hello *{user}*! Welcome to *Video Downloader Bot*\n\n"
        f"📥 I can download videos from YouTube, Facebook,\n"
        f"Instagram, TikTok, Twitter and more!\n\n"
        f"👇 *Choose a platform to get started:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return PLATFORM  # move to next state


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *How to use this bot:*\n\n"
        "1️⃣ Type /start\n"
        "2️⃣ Choose a platform (YouTube, Instagram etc.)\n"
        "3️⃣ Paste your video link\n"
        "4️⃣ Choose video quality\n"
        "5️⃣ Get your download link ✅\n\n"
        "⏳ Download links expire in *10 minutes*\n\n"
        "❌ To cancel anytime: /cancel",
        parse_mode="Markdown"
    )