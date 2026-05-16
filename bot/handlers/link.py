from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.validator import is_valid_url, detect_platform

QUALITY = 2


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Validate URL
    if not is_valid_url(url):
        await update.message.reply_text(
            "❌ *That doesn't look like a valid URL!*\n\n"
            "Please paste a proper video link.\n"
            "Example: `https://youtube.com/watch?v=xxxxx`\n\n"
            "Try again 👇",
            parse_mode="Markdown"
        )
        return QUALITY - 1  # stay on LINK state

    # Save URL in user session
    context.user_data["url"] = url

    # Auto-detect platform if needed
    detected = detect_platform(url)
    if detected:
        context.user_data["platform"] = detected

    # Show quality options
    keyboard = [
        [
            InlineKeyboardButton("🎥 1080p (Full HD)", callback_data="1080"),
            InlineKeyboardButton("📺 720p (HD)",       callback_data="720"),
        ],
        [
            InlineKeyboardButton("📱 480p (Medium)",   callback_data="480"),
            InlineKeyboardButton("📉 360p (Low)",      callback_data="360"),
        ],
        [
            InlineKeyboardButton("🔉 Audio Only (MP3)", callback_data="audio"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ *Link received!*\n\n"
        f"🔗 `{url[:60]}{'...' if len(url) > 60 else ''}`\n\n"
        "🎬 *Choose download quality:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return QUALITY  # move to next state