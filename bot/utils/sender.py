import os

# Telegram bot API max upload size = 50MB
MAX_TELEGRAM_SIZE = 100 * 1024 * 1024  # 50 MB in bytes


async def send_video_or_link(query, file_path, file_name, file_size, quality_label, download_url):
    """
    If file < 50MB → send video directly in Telegram chat
    If file > 50MB → send download link
    """

    size_mb = round(file_size / (1024 * 1024), 2)

    if file_size <= MAX_TELEGRAM_SIZE:
        # ✅ Send video directly in chat
        await query.message.reply_text(
            f"✅ *Download Ready!* ({size_mb} MB)\n"
            f"🎬 {quality_label}\n\n"
            f"👇 *Video is below — click 3 dots to save:*",
            parse_mode="Markdown"
        )

        # Send the actual video file
        with open(file_path, "rb") as video_file:
            await query.message.reply_video(
                video=video_file,
                caption=f"📁 {file_name}\n📦 {size_mb} MB | 🎬 {quality_label}\n\n🤖 @Mylocalvideo_bot",
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
            )

        # Delete file from server after sending
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Deleted after sending: {file_name}")

    else:
        # ❌ File too big for Telegram — send download link
        await query.message.reply_text(
            f"✅ *Download Ready!*\n\n"
            f"📁 `{file_name}`\n"
            f"📦 Size: {size_mb} MB _(too large to send directly)_\n"
            f"🎬 {quality_label}\n\n"
            f"👇 *Click below to download:*\n"
            f"[⬇️ Download Now]({download_url})\n\n"
            f"⏳ *Link expires in 10 minutes!*",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )