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
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ExtBot,
)
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    ParamSpec,
)

ICONS: dict[str, str] = {
    "back": "⬅️",
    "cart": "🛒",
    "catalog": "🛍️",
    "en": "🇺🇸",
    "gallery": "🖼️",
    "left": "◀️",
    "pants": "👖",
    "profile": "👤",
    "right": "▶️",
    "socks": "🧦",
    "t-shirts": "👕",
    "ua": "🇺🇦",
}

LANGUAGES: dict[str, str] = {
    "ua": "Українська",
    "en": "English",
}

P = ParamSpec("P")

PRODUCTS = {
    "t-shirts": {
        "names": {
            "en": "T-shirts",
            "ua": "Футболки",
        },
        "items": [
            {
                "description": {
                    "en": "Silhouettes, fabrics, and craftsmanship draw from the House codes and speaks to the present without losing sight of the heritage. This medium cotton jersey T-shirt is defined by a Gucci Interlocking G print with faded effect.",
                    "ua": "Силуети, тканини та майстерність черпають натхнення з кодексів Дому та відображають сьогодення, не втрачаючи з поля зору спадщину. Ця футболка з бавовняного трикотажу середньої довжини прикрашена принтом Gucci Interlocking G з вицвілим ефектом.",
                },
                "id": 829,
                "name": {
                    "en": "Cotton jersey T-shirt with print",
                    "ua": "Футболка з бавовняного трикотажу з принтом",
                },
                "photos": [
                    "images/catalog/t-shirts/gucci-1.png",
                    "images/catalog/t-shirts/gucci-2.png",
                    "images/catalog/t-shirts/gucci-3.png",
                ],
                "price": 650,
                "stock": 15,
            },
            {
                "description": {
                    "en": "Calvin Klein for men. Refined classics for a curated wardrobe. Minimalist essentials in signature silhouettes.",
                    "ua": "Calvin Klein для чоловіків. Вишукана класика для ретельно підібраного гардеробу. Мінімалістичні предмети першої необхідності у фірмових силуетах.",
                },
                "id": 614,
                "name": {
                    "en": "Monologo T-Shirt",
                    "ua": "Футболка Monologo",
                },
                "photos": [
                    "images/catalog/t-shirts/calvin-klein-1.png",
                    "images/catalog/t-shirts/calvin-klein-2.png",
                    "images/catalog/t-shirts/calvin-klein-3.png",
                ],
                "price": 75,
                "stock": 31,
            },
            {
                "description": {
                    "en": "This wardrobe essential T-shirt is made from pure cotton jersey with branded embroidery and cut to a figure-forming slim fit.",
                    "ua": "Ця незамінна футболка виготовлена ​​з чистого бавовняного трикотажу з фірмовою вишивкою та має приталений крой, що фіксує фігуру.",
                },
                "id": 614,
                "name": {
                    "en": "Logo Embroidery Jersey Slim T-Shirt",
                    "ua": "Футболка з вишивкою логотипу з джерсі",
                },
                "photos": [
                    "images/catalog/t-shirts/tommy-hilfiger-1.png",
                    "images/catalog/t-shirts/tommy-hilfiger-2.png",
                    "images/catalog/t-shirts/tommy-hilfiger-3.png",
                ],
                "price": 49.90,
                "stock": 70,
            },
        ],
    },
}

TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "add_to_cart": "Add to cart",
        "back": "Back",
        "cart": "Cart",
        "catalog": "Catalog",
        "main_welcome": "Welcome to our shop!",
        "next": "Next",
        "pants": "Pants",
        "previous": "Previous",
        "price": "Price",
        "product_caption": "{icon} Products in the <b>{category}</b> category · Page {page}/{pages}",
        "profile": "Profile",
        "select_product_category": "Select product category",
        "socks": "Socks",
        "stock": "Stock",
        "t-shirts": "T-shirts",
    },
    "ua": {
        "add_to_cart": "Додати до кошика",
        "back": "Назад",
        "cart": "Кошик",
        "catalog": "Каталог",
        "main_welcome": "Ласкаво просимо до нашого магазину!",
        "next": "Наступне",
        "pants": "Штани",
        "previous": "Попереднє",
        "price": "Ціна",
        "product_caption": "{icon} Товари в категорії <b>{category}</b> · Сторінка {page}/{pages}",
        "profile": "Профіль",
        "select_product_category": "Виберіть категорію товарів",
        "socks": "Шкарпетки",
        "stock": "В наявності",
        "t-shirts": "Футболки",
    },
}

logger: Optional[Logger] = None

user_states: dict[int, dict[str, Any]] = {}


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query
    await query.answer()

    data = query.data
    user_state = get_user_state(update)

    # Выбор языка и переход на главный экран

    if data.startswith("language:"):

        language_code = data.split(":")[1]

        if language_code in LANGUAGES:
            user_state["language"] = language_code

        await replace_screen(update, context, show_main_screen)

        return

    # Главный экран

    if data == "main":

        await replace_screen(update, context, show_main_screen)

        return

    # Выбор категории товаров

    if data == "catalog":

        await replace_screen(update, context, show_product_category_screen)

        return

    # Экран товара

    if data.startswith("catalog:"):

        await replace_screen(update, context, show_product_screen, data)

        return


async def clear_screen(bot: ExtBot, chat_id: int, state: dict[str, Any]) -> None:

    # Удаляем сообщения в обратном порядке, потому что Telegram
    # иногда выдаёт ошибку, если удалить раньше старшее сообщение
    for message_id in reversed(state["screen_message_ids"]):
        await try_delete_message(bot, chat_id, message_id)

    state["screen_message_ids"] = []


def create_user_state(user_id: int) -> dict[str, Any]:

    state = {
        "language": "ua",
        "screen_message_ids": [],
    }

    user_states[user_id] = state

    return state


def get_chat_id(update: Update) -> int:

    return update.effective_chat.id


def get_user_id(update: Update) -> int:

    return update.effective_user.id


def get_user_state(update: Update) -> dict[str, Any]:

    id = get_user_id(update)
    state = user_states.get(id)

    if state is not None:
        return state

    return create_user_state(id)


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
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    show_function: Callable[P, Awaitable[Any]],
    *args: P.args, **kwargs: P.kwargs
) -> None:

    chat_id = get_chat_id(update)
    user_state = get_user_state(update)
    await clear_screen(context.bot, chat_id, user_state)

    result = await show_function(update, context, *args, **kwargs)

    if not isinstance(result, list):
        result = [result]

    user_state["screen_message_ids"] = [
        message.message_id for message in result]


async def show_language_screen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    text = "Оберіть мову | Select language"

    buttons: list[InlineKeyboardButton] = []

    for code, title in LANGUAGES.items():
        data = f"language:{code}"
        button = InlineKeyboardButton(
            text=f"{ICONS[code]} {title}",
            callback_data=data)
        buttons.append(button)

    keys = InlineKeyboardMarkup([buttons])
    chat_id = get_chat_id(update)

    message = await context.bot.send_message(
        chat_id=chat_id, reply_markup=keys, text=text)

    return message


async def show_main_screen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_state = get_user_state(update)
    chat_id = get_chat_id(update)

    language = user_state["language"]
    texts = TEXTS[language]

    photo = "./images/lux-rags.png"
    caption = texts["main_welcome"]

    keys = InlineKeyboardMarkup([[
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

    return await context.bot.send_photo(
        caption=caption,
        chat_id=chat_id,
        photo=photo,
        reply_markup=keys,
    )


async def show_product_category_screen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_state = get_user_state(update)
    chat_id = get_chat_id(update)

    language = user_state["language"]
    texts = TEXTS[language]

    text = texts["select_product_category"]

    button_data: dict[str, tuple[str, str]] = dict(sorted({
        texts["t-shirts"]: (ICONS["t-shirts"], "catalog:t-shirts"),
        texts["pants"]: (ICONS["pants"], "catalog:pants"),
        texts["socks"]: (ICONS["socks"], "catalog:socks"),
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

    return await context.bot.send_message(
        chat_id=chat_id,
        reply_markup=reply_markup,
        text=text,
    )


async def show_product_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):

    chat_id = get_chat_id(update)
    state = get_user_state(update)

    language = state["language"]
    texts = TEXTS[language]

    parts = data.split(":")
    category_key = parts[1]
    page = int(parts[2]) if len(parts) >= 3 else 1
    photo = int(parts[3]) if len(parts) == 4 else 1

    category = PRODUCTS[category_key]
    category_name = category["names"][language]
    pages = len(category["items"])

    icon = ICONS["catalog"]
    caption = texts["product_caption"].format(
        icon=icon, category=category_name, page=page, pages=pages)

    messages = []

    message = await context.bot.send_message(
        chat_id=chat_id,
        parse_mode="HTML",
        text=caption,
    )

    messages.append(message)

    product = category["items"][page - 1]
    product_id = product["id"]
    photos = len(product["photos"])
    photo_path = product["photos"][photo - 1]
    product_name = product["name"][language]
    product_description = product["description"][language]
    product_price = product["price"]
    product_stock = product["stock"]
    price_label = texts["price"]
    stock_label = texts["stock"]

    caption = (
        f"<b>{product_name}</b>\n\n"
        f"<i>{product_description}</i>\n\n"
        f"<b>{price_label}:</b> ${product_price}\n"
        f"<b>{stock_label}:</b> {product_stock}"
    )

    previous_page = page - 1
    if previous_page == 0:
        previous_page = pages

    next_page = page + 1
    if next_page > pages:
        next_page = 1

    next_photo = photo + 1
    if next_photo > photos:
        next_photo = 1

    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text=f"{ICONS["cart"]} {texts["add_to_cart"]}",
            callback_data=f"cart:{product_id}")
    ], [
        InlineKeyboardButton(
            text=f"{ICONS["left"]} {texts["previous"]}",
            callback_data=f"catalog:{category_key}:{previous_page}:1"),
        InlineKeyboardButton(
            text=f"{ICONS["gallery"]} {photo}/{photos}",
            callback_data=f"catalog:{category_key}:{page}:{next_photo}"),
        InlineKeyboardButton(
            text=f"{ICONS["right"]} {texts["next"]}",
            callback_data=f"catalog:{category_key}:{next_page}:1"),
    ], [
        InlineKeyboardButton(
            text=f"{ICONS["back"]} {texts["back"]}",
            callback_data=f"catalog")
    ]])

    message = await context.bot.send_photo(
        caption=caption,
        chat_id=chat_id,
        parse_mode="HTML",
        photo=photo_path,
        reply_markup=buttons,
    )

    messages.append(message)

    return messages


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    await replace_screen(update, context, show_language_screen)


async def try_delete_message(bot: ExtBot, chat_id: int, message_id: int) -> None:

    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as exception:
        logger.warning(
            f"Failed to delete message {message_id} in chat {chat_id}: {exception}")


if __name__ == "__main__":
    main()
