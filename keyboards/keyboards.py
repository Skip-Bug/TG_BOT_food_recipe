from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_IDS


def main_menu(user_id):
    kb = [
        [InlineKeyboardButton("🍽 Рецепт", callback_data="random_recipe")],
        [InlineKeyboardButton("⭐ Избранное", callback_data="favorites")],
        [InlineKeyboardButton("💰 Подписка", callback_data="subscribe")]
    ]

    if user_id in ADMIN_IDS:
        kb.append([InlineKeyboardButton("👑 Админка", callback_data="admin_panel")])

    return InlineKeyboardMarkup(kb)


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить", callback_data="add_recipe")],
        [InlineKeyboardButton("📋 Список", callback_data="recipe_list")],
        [InlineKeyboardButton("🗑 Удалить", callback_data="delete_recipe")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ])