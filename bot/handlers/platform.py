from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

LINK = 1

PLATFORM_NAMES = {
    "youtube":   "YouTube 🎬",
    "facebook":  "Facebook 📘",
    "instagram": "Instagram 📸",
    "tiktok":    "TikTok 🎵",
    "twitter":   "Twitter/X 🐦",
    "other":     "Direct URL 🔗",
}

PLATFORM_EXAMPLES = {
    "youtube":   "https://youtube.com/watch?v=xxxxx",
    "facebook":  "https://facebook.com/video/xxxxx",
    "instagram": "https://instagram.com/reel/xxxxx",
    "tiktok":    "https://tiktok.com/@user/video/xxxxx",
    "twitter":   "https://twitter.com/user/status/xxxxx",
    "other":     "https://example.com/video.mp4",
}


async def platform_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    platform = query.data
    context.user_data["platform"] = platform

    name    = PLATFORM_NAMES.get(platform, platform)
    example = PLATFORM_EXAMPLES.get(platform, "")

    await query.edit_message_text(
        f"✅ Platform selected: *{name}*\n\n"
        f"🔗 Now *paste your video link* below:\n\n"
        f"📌 Example:\n`{example}`\n\n"
        f"❌ To cancel: /cancel",
        parse_mode="Markdown"
    )

    return LINK  # move to next state