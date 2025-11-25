import logging

from dotenv import load_dotenv
from os import getenv
from typing import List

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

LANGS = {
    "ru": "🇺🇦 Українська",
    "en": "🇺🇸 English",
}

logging.basicConfig(
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main():
    load_dotenv()
    BOT_TOKEN = getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    logger.info("Bot started...")
    app.run_polling()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await show_language_screen(chat_id, context)


async def show_language_screen(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE
) -> None:
    text = "Оберіть мову | Choose language"
    buttons: List[InlineKeyboardButton] = []

    for code, title in LANGS.items():
        data = f"lang_{code}"
        button = InlineKeyboardButton(title, callback_data=data)
        buttons.append(button)

    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])

    await context.bot.send_message(
        chat_id=chat_id,
        reply_markup=markup,
        text=text,
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


if __name__ == "__main__":
    main()
