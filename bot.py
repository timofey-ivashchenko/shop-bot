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

LANGUAGES: dict[str, str] = {
    "ua": "Українська",
    "en": "English",
}


TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "back": "Back",
        "cart": "Cart",
        "catalog": "Catalog",
        "main_welcome": "Welcome to our shop!",
        "pants": "Pants",
        "profile": "Profile",
        "select_product_category": "Select product category",
        "socks": "Socks",
        "t-shirts": "T-shirts",
    },
    "ua": {
        "back": "Назад",
        "cart": "Кошик",
        "catalog": "Каталог",
        "main_welcome": "Ласкаво просимо до нашого магазину!",
        "pants": "Штани",
        "profile": "Профіль",
        "select_product_category": "Виберіть категорію товарів",
        "socks": "Шкарпетки",
        "t-shirts": "Футболки",
    },
}

ICONS: dict[str, str] = {
    "back": "⬅️",
    "cart": "🛒",
    "catalog": "🛍️",
    "en": "🇺🇸",
    "pants": "👖",
    "profile": "👤",
    "socks": "🧦",
    "t-shirts": "👕",
    "ua": "🇺🇦",
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

    # Выбор категории товаров

    if data == "catalog":

        await replace_screen(
            chat_id=chat_id,
            context=context,
            message_to_delete=message,
            show_function=show_product_category_screen,
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

    text = "Оберіть мову | Select language"

    buttons: list[InlineKeyboardButton] = []

    for code, title in LANGUAGES.items():
        icon = ICONS[code]
        caption = f"{icon} {title}"
        data = f"language_{code}"
        button = InlineKeyboardButton(
            text=caption,
            callback_data=data)
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
            text=f"{ICONS["catalog"]} {texts["catalog"]}",
            callback_data="catalog"),
        InlineKeyboardButton(
            text=f"{ICONS["cart"]} {texts["cart"]}",
            callback_data="cart"),
        InlineKeyboardButton(
            text=f"{ICONS["profile"]} {texts["profile"]}",
            callback_data="profile"),
    ]])

    await context.bot.send_photo(
        caption=caption,
        chat_id=chat_id,
        photo=photo,
        reply_markup=reply_markup,
    )


async def show_product_category_screen(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    user_state: dict[str, Any]
) -> None:

    language = user_state["language"]
    texts = TEXTS[language]

    text = texts["select_product_category"]

    button_data: dict[str, tuple[str, str]] = dict(sorted({
        texts["t-shirts"]: (ICONS["t-shirts"], "catalog_t-shirts"),
        texts["pants"]: (ICONS["pants"], "catalog_pants"),
        texts["socks"]: (ICONS["socks"], "catalog_socks"),
    }.items()))

    buttons: list[list[InlineKeyboardButton]] = []

    for title, data in button_data.items():
        buttons.append([InlineKeyboardButton(
            text=f"{data[0]} {title}",
            callback_data=data[1])])

    buttons.append([InlineKeyboardButton(
        text=f"{ICONS["back"]} {texts["back"]}",
        callback_data="main")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await context.bot.send_message(
        chat_id=chat_id,
        reply_markup=reply_markup,
        text=text,
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_id = update.effective_user.id
    get_or_create_user_state(user_id)

    chat_id = update.effective_chat.id
    await show_language_screen(chat_id, context)

if __name__ == "__main__":
    main()
