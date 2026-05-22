from telegram import Update
from telegram.ext import ContextTypes

from keyboards.keyboards import main_menu

from services.json_db import (
    load_users,
    save_users,
    get_user
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tg_id = str(update.effective_user.id)

    if get_user(tg_id) is None:

        users = load_users()

        users.append({

            "tg_id": tg_id,

            "subscriber": False,

            "recipes_viewed": 0,

            "favorites": []
        })

        save_users(users)

    await update.message.reply_text(
        "🍽 Добро пожаловать в FoodPlan!",
        reply_markup=main_menu()
    )
