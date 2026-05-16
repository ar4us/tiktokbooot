import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config
from core import logger as async_logger
from handlers.message_handler import start, handle_message
from handlers.callback_handler import handle_callback

async def main():
    # 1. Setup config and logging
    try:
        Config.validate()
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Start async logging drain
    drain_task = asyncio.create_task(async_logger.setup(Config.LOG_LEVEL))
    logger = logging.getLogger(__name__)
    
    # 2. Build application
    logger.info("Building application...")
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # 3. Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # 4. Run bot
    logger.info("Starting bot polling...")
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        drain_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
