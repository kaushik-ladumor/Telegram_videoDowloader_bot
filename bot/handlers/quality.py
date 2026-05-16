from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.downloader import download_video
from utils.api import create_download_link
import asyncio

PLATFORM = 0


async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality  = query.data
    url      = context.user_data.get("url")
    platform = context.user_data.get("platform", "other")

    if not url:
        await query.edit_message_text("❌ Something went wrong. Please start again with /start")
        return ConversationHandler.END

    # Show processing message
    quality_label = {
        "1080":  "1080p Full HD 🎥",
        "720":   "720p HD 📺",
        "480":   "480p Medium 📱",
        "360":   "360p Low 📉",
        "audio": "Audio Only MP3 🔉",
    }.get(quality, quality)

    await query.edit_message_text(
        f"⏳ *Processing your download...*\n\n"
        f"🔗 URL: `{url[:50]}...`\n"
        f"🎬 Quality: {quality_label}\n\n"
        f"Please wait, this may take 30-60 seconds...",
        parse_mode="Markdown"
    )

    try:
        # Download the video
        file_path, file_name, file_size = await asyncio.get_event_loop().run_in_executor(
            None, download_video, url, quality
        )

        # Create expiring download link via Node.js server
        download_url = await create_download_link(file_path, file_name)

        size_mb = round(file_size / (1024 * 1024), 2) if file_size else "?"

        await query.edit_message_text(
            f"✅ *Your download is ready!*\n\n"
            f"📁 File: `{file_name}`\n"
            f"📦 Size: {size_mb} MB\n"
            f"🎬 Quality: {quality_label}\n\n"
            f"👇 *Click below to download:*\n"
            f"[⬇️ Download Now]({download_url})\n\n"
            f"⏳ *Link expires in 10 minutes!*\n"
            f"🔄 Start again: /start",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        error_msg = str(e)
        print(f"Download error: {error_msg}")

        await query.edit_message_text(
            f"❌ *Download failed!*\n\n"
            f"Reason: {error_msg[:100]}\n\n"
            f"Possible reasons:\n"
            f"• Video is private or age-restricted\n"
            f"• Platform blocked the download\n"
            f"• Invalid or expired link\n\n"
            f"🔄 Try again: /start",
            parse_mode="Markdown"
        )

    # Clear user session data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ *Cancelled!*\n\nType /start to begin again.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END