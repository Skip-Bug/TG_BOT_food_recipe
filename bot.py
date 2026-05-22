import logging

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)
from telegram.error import Forbidden
from telegram.request import HTTPXRequest

from config import TOKEN
from states.states import *
from handlers.user import start
from handlers.callbacks import button_handler
from handlers.admin import (
    add_recipe_start, add_title, add_description,
    add_ingredients, add_image, cancel
)


async def error_handler(update, context):
    if isinstance(context.error, Forbidden):
        logger.warning("Пользователь заблокировал бота: %s", update)
    else:
        logger.error("Ошибка: %s", context.error)


def main():
    request = HTTPXRequest(
    connection_pool_size=8,
    pool_timeout=30.0,
    connect_timeout=30.0,
    read_timeout=30.0,
    write_timeout=30.0,
    )
    app = Application.builder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_recipe_start, pattern="^add_recipe$")],
        states={
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            ADD_INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ingredients)],
            ADD_IMAGE: [MessageHandler(filters.PHOTO, add_image)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )
    app.add_handler(conv)

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_error_handler(error_handler)

    print("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
