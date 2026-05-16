import logging
import hashlib
from telegram import Update
from telegram.ext import ContextTypes
from utils.validator import URLValidator
from services.extractor import TikTokExtractor
from services.analyzer import MediaAnalyzer
from services.insight import InsightBuilder
from utils.formatter import TelegramFormatter

logger = logging.getLogger(__name__)
extractor = TikTokExtractor()
analyzer = MediaAnalyzer()
builder = InsightBuilder()
formatter = TelegramFormatter()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Welcome to TikTok Analyzer Bot!\n\n"
        "Send me a TikTok URL to analyze its performance and download it without watermark."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and URLs."""
    text = update.message.text
    if not text:
        return

    url = URLValidator.get_url(text)
    if not url:
        await update.message.reply_text(
            "❌ Please send a valid TikTok URL.\n"
            "Example: https://www.tiktok.com/@user/video/123456789"
        )
        return

    logger.info(f"Received valid TikTok URL: {url}")
    status_msg = await update.message.reply_text("🔍 Extracting information...")

    logger.info(f"Extracting info for {url}...")
    engagement_data = await extractor.extract_info(url)
    if not engagement_data:
        logger.warning(f"Extraction failed for {url}")
        await status_msg.edit_text("❌ Failed to extract information.")
        return

    logger.info(f"Analyzing media for {url}...")
    await status_msg.edit_text("⚙️ Analyzing video quality...")
    tech_data = await analyzer.analyze(
        engagement_data.video_url, 
        engagement_data.formats, 
        title=engagement_data.title or engagement_data.description,
        headers=engagement_data.http_headers
    )

    logger.info(f"Building report for {url}...")
    await status_msg.edit_text("🧠 Generating insights...")
    report = builder.build(engagement_data, tech_data)

    # Manage URL map for callbacks
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    if 'url_map' not in context.bot_data:
        context.bot_data['url_map'] = {}
    context.bot_data['url_map'][url_hash] = url

    logger.info(f"Formatting report for {url}...")
    report_text, reply_markup = formatter.format_report(report, url_hash)
    
    try:
        await status_msg.delete()
    except Exception:
        pass

    try:
        await update.message.reply_text(
            report_text, 
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send HTML message: {e}")
        # Fallback to plain text if HTML fails
        await update.message.reply_text(
            "❌ Error rendering report. Sending raw statistics instead.\n\n" + 
            report_text.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', ''), # Primitive unescape
            reply_markup=reply_markup
        )

