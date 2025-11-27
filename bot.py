from dotenv import (
    load_dotenv
)
from logging import (
    INFO,
    Logger,
    basicConfig,
    getLogger,
)
from os import (
    getenv
)
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    ParamSpec,
)

P = ParamSpec("P")

LANGUAGES = {
    "ua": "🇺🇦 Українська",
    "en": "🇺🇸 English",
}


TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "cart": "Cart",
        "catalog": "Catalog",
        "main_welcome": "Welcome to our shop!",
        "profile": "Profile",
    },
    "ua": {
        "cart": "Кошик",
        "catalog": "Каталог",
        "main_welcome": "Ласкаво просимо до нашого магазину!",
        "profile": "Профіль",
    },
}

logger: Optional[Logger] = None

user_states: dict[int, dict[str, Any]] = {}


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user
    message = query.message
    chat_id = message.chat.id

    user_state = get_or_create_user_state(user.id)

    # Выбор языка

    if data.startswith("language_"):

        language_code = data.split("_")[1]

        if language_code in LANGUAGES:
            user_state["language"] = language_code

        await replace_screen(
            chat_id=chat_id,
            context=context,
            message_to_delete=message,
            show_function=show_main_screen,
            user_state=user_state,
        )

        return


def get_or_create_user_state(user_id: int) -> dict[str, Any]:

    state = user_states.get(user_id)

    if state is None:
        state = {"language": "ua"}

    user_states[user_id] = state

    return state


def init_logger() -> Logger:

    log_message_format = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    basicConfig(format=log_message_format, level=INFO)

    return getLogger(name=__name__)


def main() -> None:

    load_dotenv()
    token = getenv(key="BOT_TOKEN")

    app = ApplicationBuilder().token(token=token).build()
    app.add_handler(CommandHandler(command="start", callback=start_handler))
    app.add_handler(CallbackQueryHandler(callback=callback_handler))

    global logger
    logger = init_logger()
    logger.info(msg="Bot started...")

    app.run_polling()


async def replace_screen(
    message_to_delete: Message,
    show_function: Callable[P, Awaitable[Any]],
    *args: P.args, **kwargs: P.kwargs
) -> None:

    try:
        await message_to_delete.delete()
    except Exception as exception:
        logger.warning("Failed to delete message: %s", exception)

    await show_function(*args, **kwargs)


async def show_language_screen(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:

    text = "Оберіть мову | Choose language"

    buttons: list[InlineKeyboardButton] = []

    for code, title in LANGUAGES.items():
        data = f"language_{code}"
        button = InlineKeyboardButton(text=title, callback_data=data)
        buttons.append(button)

    reply_markup = InlineKeyboardMarkup(inline_keyboard=[buttons])

    await context.bot.send_message(
        chat_id=chat_id,
        reply_markup=reply_markup,
        text=text,
    )


async def show_main_screen(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    user_state: dict[str, Any]
) -> None:

    language = user_state["language"]
    texts = TEXTS[language]

    photo = ".\\images\\lux-rags.png"
    caption = texts["main_welcome"]

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text=f"🛍️ {texts["catalog"]}",
            callback_data="catalog"),
        InlineKeyboardButton(
            text=f"🛒 {texts["cart"]}",
            callback_data="cart"),
        InlineKeyboardButton(
            text=f"👤 {texts["profile"]}",
            callback_data="profile"),
    ]])

    await context.bot.send_photo(
        caption=caption,
        chat_id=chat_id,
        photo=photo,
        reply_markup=reply_markup,
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_id = update.effective_user.id
    get_or_create_user_state(user_id)

    chat_id = update.effective_chat.id
    await show_language_screen(chat_id, context)


if __name__ == "__main__":
    main()
