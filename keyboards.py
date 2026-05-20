from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("🍽 Случайный рецепт", callback_data="random_recipe")],
        [InlineKeyboardButton("⭐ Избранное", callback_data="favorites")],
        [InlineKeyboardButton("💰 Подписка", callback_data="subscribe")],
        [InlineKeyboardButton("💸 Фильтр по цене", callback_data="set_price_filter")],
        [InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def recipe_actions(recipe_id, is_favorite=False):
    """Кнопки под рецептом"""
    fav_text = "❤️ Убрать из избранного" if is_favorite else "🤍 В избранное"
    keyboard = [
        [InlineKeyboardButton(fav_text, callback_data=f"toggle_fav_{recipe_id}")],
        [InlineKeyboardButton("📋 Список покупок", callback_data=f"shopping_list_{recipe_id}")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def price_filter_menu(current_filter=None):
    """Меню установки фильтра по цене"""
    status = f"💰 Текущий фильтр: до {current_filter} руб" if current_filter else "💰 Фильтр не установлен"
    keyboard = [
        [InlineKeyboardButton("200 руб", callback_data="price_200"),
         InlineKeyboardButton("500 руб", callback_data="price_500"),
         InlineKeyboardButton("1000 руб", callback_data="price_1000")],
        [InlineKeyboardButton("1500 руб", callback_data="price_1500"),
         InlineKeyboardButton("2000 руб", callback_data="price_2000"),
         InlineKeyboardButton("♾ Без фильтра", callback_data="price_clear")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu():
    """Админ-меню (только для админов)"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить рецепт", callback_data="admin_add_recipe")],
        [InlineKeyboardButton("❌ Удалить рецепт", callback_data="admin_delete_recipe")],
        [InlineKeyboardButton("📋 Список рецептов", callback_data="admin_list_recipes")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    """Только кнопка назад"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(keyboard)

def cancel_button():
    """Кнопка отмены (для состояний ожидания ввода)"""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)