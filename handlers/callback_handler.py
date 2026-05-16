import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from services.extractor import TikTokExtractor
from config import Config

logger = logging.getLogger(__name__)
extractor = TikTokExtractor()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data:
        return

    # context.bot_data should have 'url_map' : { hash: url }
    url_map = context.bot_data.get('url_map', {})
    
    if data.startswith("dl_vid_"):
        url_hash = data.replace("dl_vid_", "")
        url = url_map.get(url_hash)
        if not url:
            await query.message.reply_text("❌ Error: Download link expired. Please send the URL again.")
            return
        
        await query.message.reply_text("📥 Downloading video... please wait.")
        logger.info(f"Downloading video for {url}...")
        file_path = await extractor.download(url, mode='video')
        if file_path and os.path.exists(file_path):
            try:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                logger.info(f"Video downloaded: {file_path} ({size_mb:.2f}MB)")
                
                if size_mb > Config.MAX_FILE_MB:
                    await query.message.reply_text(f"⚠️ Video too large ({size_mb:.1f}MB) to send via Telegram bot (max {Config.MAX_FILE_MB}MB).")
                    return

                logger.info(f"Sending video to user...")
                with open(file_path, 'rb') as f:
                    await query.message.reply_video(
                        video=f, 
                        caption="✅ Video downloaded",
                        write_timeout=120, # Increase timeout for slow uploads
                        read_timeout=120
                    )
                logger.info(f"Video sent successfully.")
            except Exception as e:
                logger.error(f"Error sending video: {e}", exc_info=True)
                await query.message.reply_text("❌ Failed to send video.")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            await query.message.reply_text("❌ Failed to download video.")

    elif data.startswith("dl_aud_"):
        url_hash = data.replace("dl_aud_", "")
        url = url_map.get(url_hash)
        if not url:
            await query.message.reply_text("❌ Error: Link expired.")
            return

        await query.message.reply_text("📥 Extracting audio... please wait.")
        logger.info(f"Downloading audio for {url}...")
        file_path = await extractor.download(url, mode='audio')
        if file_path and os.path.exists(file_path):
            try:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                logger.info(f"Audio extracted: {file_path} ({size_mb:.2f}MB)")

                if size_mb > Config.MAX_FILE_MB:
                    await query.message.reply_text(f"⚠️ Audio too large ({size_mb:.1f}MB) to send.")
                    return

                logger.info(f"Sending audio to user...")
                with open(file_path, 'rb') as f:
                    await query.message.reply_audio(
                        audio=f, 
                        title="TikTok Audio",
                        write_timeout=120,
                        read_timeout=120
                    )
                logger.info(f"Audio sent successfully.")
            except Exception as e:
                logger.error(f"Error sending audio: {e}", exc_info=True)
                await query.message.reply_text("❌ Failed to send audio.")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            await query.message.reply_text("❌ Failed to extract audio.")

    elif data == "list_qual":
        await query.message.reply_text("📋 More quality options coming soon!")


