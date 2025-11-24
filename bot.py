from dotenv import load_dotenv
from os import getenv
from telegram import (
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

def main():
    load_dotenv()
    BOT_TOKEN = getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

if __name__ == "__main__":
    main()
