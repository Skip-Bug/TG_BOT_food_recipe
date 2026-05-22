from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_IDS
from services.json_db import get_user


def main_menu(user_id):
    user = get_user(str(user_id))
    role = user.get("role", "user") if user else "user"

    buttons = [
        [InlineKeyboardButton("🍽 Рецепт", callback_data="random_recipe")],
    ]

    if role in ("subscriber", "admin"):
        buttons.append([InlineKeyboardButton("⭐ Избранное", callback_data="favorites")])
    else:
        buttons.append([InlineKeyboardButton("💳 Купить подписку", callback_data="subscribe")])

    if role == "admin":
        buttons.append([InlineKeyboardButton("👑 Админка", callback_data="admin_panel")])

    return InlineKeyboardMarkup(buttons)


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить", callback_data="add_recipe")],
        [InlineKeyboardButton("📋 Список", callback_data="recipe_list")],
        [InlineKeyboardButton("🗑 Удалить", callback_data="delete_recipe")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
    ])


def recipe_menu(user_id, recipe_id, is_favorite=False):
    user = get_user(str(user_id))
    role = user.get("role", "user") if user else "user"

    buttons = [
        [InlineKeyboardButton("🔀 Другой рецепт", callback_data="random_recipe")],
    ]

    if role in ("subscriber", "admin"):
        fav_btn = (
            InlineKeyboardButton("💔 Убрать из избранного", callback_data=f"unfav_{recipe_id}")
            if is_favorite else
            InlineKeyboardButton("❤️ В избранное", callback_data=f"fav_{recipe_id}")
        )
        buttons.append([fav_btn])

    buttons.append([InlineKeyboardButton("⬅️ Меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(buttons)


def subscribe_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Купить подписку — 199₽/мес", callback_data="buy_subscribe")]
    ])
