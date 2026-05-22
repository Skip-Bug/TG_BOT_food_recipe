from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(subscriber: bool, recipes_viewed: int):
    """
    Обычный (free):
      - до 3 рецептов: [Случайный рецепт] [Подписка]
      - после 3:        [Подписка]
    Премиум:
      [Случайный рецепт] [Избранное]
      [Фильтр по цене]   [Подписка ✅]
    """
    if subscriber:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🍽 Случайный рецепт", callback_data="random_recipe")],
            [InlineKeyboardButton("⭐ Избранное",         callback_data="favorites")],
            [InlineKeyboardButton("💸 Фильтр по цене",   callback_data="set_price_filter")],
            [InlineKeyboardButton("✅ Подписка активна", callback_data="sub_info")],
        ])
    elif recipes_viewed < 3:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🍽 Случайный рецепт", callback_data="random_recipe")],
            [InlineKeyboardButton("💰 Подписка",         callback_data="subscribe")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Оформить подписку", callback_data="subscribe")],
        ])


def recipe_menu_free(recipe_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Ещё рецепт", callback_data="random_recipe")],
        [InlineKeyboardButton("⬅️ Назад",      callback_data="back_to_menu")],
    ])


def recipe_menu_premium(recipe_id, in_favorites=False):
    fav_text = "❤️ Убрать из избранного" if in_favorites else "🤍 В избранное"
    fav_cb   = f"unfav_{recipe_id}"      if in_favorites else f"fav_{recipe_id}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(fav_text,          callback_data=fav_cb)],
        [InlineKeyboardButton("🔄 Ещё рецепт",  callback_data="random_recipe")],
        [InlineKeyboardButton("⬅️ Назад",        callback_data="back_to_menu")],
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить рецепт",  callback_data="add_recipe")],
        [InlineKeyboardButton("📋 Список рецептов",  callback_data="recipe_list")],
        [InlineKeyboardButton("🗑 Удалить рецепт",   callback_data="delete_recipe")],
        [InlineKeyboardButton("⬅️ Главное меню",     callback_data="back_to_menu")],
    ])


def price_filter_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("200₽",  callback_data="price_200"),
            InlineKeyboardButton("500₽",  callback_data="price_500"),
            InlineKeyboardButton("1000₽", callback_data="price_1000"),
        ],
        [
            InlineKeyboardButton("1500₽",         callback_data="price_1500"),
            InlineKeyboardButton("2000₽",         callback_data="price_2000"),
            InlineKeyboardButton("♾ Без фильтра", callback_data="price_clear"),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")],
    ])


def cancel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отменить добавление", callback_data="cancel_add")],
    ])
