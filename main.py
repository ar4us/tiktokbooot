import asyncio
import logging
import os
from aiohttp import web
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config
from core import logger as async_logger
from handlers.message_handler import start, handle_message
from handlers.callback_handler import handle_callback

async def health_check(request):
    return web.Response(text="OK")

async def start_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.getLogger(__name__).info(f"Dummy web server listening on port {port}")

async def post_init(application):
    # Start async logging drain
    application.bot_data['drain_task'] = asyncio.create_task(async_logger.setup(Config.LOG_LEVEL))
    
    # Start dummy web server for Railway healthcheck
    await start_dummy_server()
    
    logging.getLogger(__name__).info("Bot application initialized.")

def main():
    # 1. Setup config
    try:
        Config.validate()
    except ValueError as e:
        print(f"Error: {e}")
        return

    logger = logging.getLogger(__name__)
    
    # 2. Build application
    print("Building application...")
    application = ApplicationBuilder().token(Config.BOT_TOKEN).post_init(post_init).build()

    # 3. Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # 4. Run bot
    print("Starting bot polling...")
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
