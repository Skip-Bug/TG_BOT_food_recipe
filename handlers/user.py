import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from keyboards.keyboards import main_menu, subscribe_menu
from services.json_db import (
    load_recipes, get_user,
    increase_views, can_view_recipe, register_user
)

logger = logging.getLogger(__name__)

SUBSCRIBE_TEXT = (
    "⛔ Вы использовали все 3 бесплатных рецепта.\n\n"
    "🌟 Подписка FoodPlan — 199₽/мес\n\n"
    "Что вы получите:\n"
    "• 🍽 Безлимитный доступ ко всем рецептам\n"
    "• ⭐ Избранное — сохраняйте любимые блюда\n"
    "• 💰 Расчёт стоимости каждого блюда\n"
    "• 🛒 Готовый список ингредиентов\n"
    "• 🆕 Новые рецепты каждую неделю\n\n"
    "Оформите подписку и готовьте без ограничений! 👇"
)


def build_recipe_text(recipe):
    ing_text = ""
    total = 0
    for i in recipe["ingredients"]:
        ing_text += f"• {i['title']} ({i['amount']}) - {i['price']}₽\n"
        total += i["price"]
    return (
        f"🍽 {recipe['title']}\n\n"
        f"{recipe['description']}\n\n"
        f"💰 {total}₽\n\n"
        f"{ing_text}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = str(update.effective_user.id)
    is_admin = update.effective_user.id in ADMIN_IDS

    register_user(tg_id, is_admin=is_admin)

    user = get_user(tg_id)
    role = user.get("role", "user") if user else "user"
    recipes_viewed = user.get("recipes_viewed", 0) if user else 0

    if role == "admin":
        await update.message.reply_text("🍽 Добро пожаловать в FoodPlan!\n\n👑 Вы вошли как администратор.")
    elif role == "subscriber":
        await update.message.reply_text("🍽 Добро пожаловать в FoodPlan!\n\n✅ У вас активна подписка.")
    else:
        remaining = max(0, 3 - recipes_viewed)
        await update.message.reply_text(
            "🍽 Добро пожаловать в FoodPlan!\n\n"
            "⚠️ Вы используете бесплатную версию бота.\n"
            f"У вас осталось {remaining} из 3 бесплатных рецептов.\n\n"
            "Оформите подписку, чтобы получить безлимитный доступ! 👇",
            reply_markup=subscribe_menu() if remaining == 0 else None
        )

    recipes = load_recipes()
    if not recipes:
        await update.message.reply_text("📭 Нет рецептов")
        return

    if not can_view_recipe(tg_id):
        await update.message.reply_text(SUBSCRIBE_TEXT, reply_markup=subscribe_menu())
        return

    recipe = random.choice(recipes)
    increase_views(tg_id)
    text = build_recipe_text(recipe)

    await update.message.reply_photo(
        photo=recipe["photo"],
        caption=text,
        reply_markup=main_menu(update.effective_user.id)
    )
