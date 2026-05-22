import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from services.json_db import (
    load_recipes,
    save_recipes,
    can_view_recipe,
    increase_views,
    set_subscriber,
    add_to_favorites,
    remove_from_favorites,
    get_favorites,
    get_user
)
from keyboards.keyboards import main_menu, admin_menu, recipe_menu, subscribe_menu

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


async def safe_edit(query, text, reply_markup=None):
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception:
        try:
            await query.edit_message_caption(text, reply_markup=reply_markup)
        except Exception:
            await query.message.reply_text(text, reply_markup=reply_markup)


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_panel":
        if query.from_user.id not in ADMIN_IDS:
            await safe_edit(query, "⛔ Нет доступа")
            return
        await safe_edit(query, "👑 Админ-панель", reply_markup=admin_menu())

    elif data == "back_to_menu":
        await safe_edit(query, "Главное меню", reply_markup=main_menu(query.from_user.id))

    elif data == "random_recipe":
        recipes = load_recipes()
        if not recipes:
            await safe_edit(query, "Нет рецептов")
            return
        if not can_view_recipe(query.from_user.id):
            await safe_edit(query, SUBSCRIBE_TEXT, reply_markup=subscribe_menu())
            return
        recipe = random.choice(recipes)
        increase_views(query.from_user.id)
        text = build_recipe_text(recipe)
        fav_ids = get_favorites(query.from_user.id)
        await query.message.reply_photo(
            photo=recipe["photo"],
            caption=text,
            reply_markup=recipe_menu(
                query.from_user.id,
                recipe["id"],
                is_favorite=recipe["id"] in fav_ids
            )
        )

    elif data == "recipe_list":
        recipes = load_recipes()
        if not recipes:
            await safe_edit(query, "📭 Рецептов пока нет")
            return
        text = "📋 Рецепты:\n\n"
        for recipe in recipes:
            total = sum(i["price"] for i in recipe["ingredients"])
            text += f"{recipe['id']}. {recipe['title']} ({total}₽)\n"
        await safe_edit(query, text, reply_markup=admin_menu())

    elif data == "delete_recipe":
        recipes = load_recipes()
        keyboard = []
        for recipe in recipes:
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {recipe['title']}",
                    callback_data=f"delete_{recipe['id']}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="admin_panel")
        ])
        await safe_edit(
            query,
            "Выберите рецепт для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("delete_"):
        recipe_id = int(data.split("_")[1])
        recipes = load_recipes()
        recipes = [r for r in recipes if r["id"] != recipe_id]
        save_recipes(recipes)
        await safe_edit(query, "✅ Рецепт удалён", reply_markup=admin_menu())

    elif data.startswith("fav_"):
        recipe_id = int(data.split("_")[1])
        add_to_favorites(query.from_user.id, recipe_id)
        await query.answer("❤️ Добавлено в избранное!", show_alert=False)

    elif data.startswith("unfav_"):
        recipe_id = int(data.split("_")[1])
        remove_from_favorites(query.from_user.id, recipe_id)
        await query.answer("💔 Убрано из избранного", show_alert=False)

    elif data == "favorites":
        user = get_user(str(query.from_user.id))
        if not user or not user.get("subscriber", False):
            await safe_edit(query, SUBSCRIBE_TEXT, reply_markup=subscribe_menu())
            return

        fav_ids = get_favorites(query.from_user.id)
        if not fav_ids:
            await safe_edit(
                query,
                "⭐ У вас пока нет избранных рецептов",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Меню", callback_data="back_to_menu")]
                ])
            )
            return
        recipes = load_recipes()
        fav_recipes = [r for r in recipes if r["id"] in fav_ids]
        if not fav_recipes:
            await safe_edit(query, "⭐ Избранные рецепты не найдены")
            return
        kb = [
            [InlineKeyboardButton(f"🍽 {r['title']}", callback_data=f"show_{r['id']}")]
            for r in fav_recipes
        ]
        kb.append([InlineKeyboardButton("⬅️ Меню", callback_data="back_to_menu")])
        await safe_edit(query, "⭐ Избранное:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("show_"):
        recipe_id = int(data.split("_")[1])
        recipes = load_recipes()
        recipe = next((r for r in recipes if r["id"] == recipe_id), None)
        if not recipe:
            await query.answer("Рецепт не найден", show_alert=True)
            return
        fav_ids = get_favorites(query.from_user.id)
        text = build_recipe_text(recipe)
        await query.message.reply_photo(
            photo=recipe["photo"],
            caption=text,
            reply_markup=recipe_menu(query.from_user.id, recipe_id, is_favorite=True)
        )

    elif data in ("subscribe", "buy_subscribe"):
        set_subscriber(query.from_user.id)
        await safe_edit(
            query,
            "✅ Подписка активирована!\n\n"
            "Теперь вам доступны:\n"
            "• 🍽 Безлимитные рецепты\n"
            "• ⭐ Избранное\n\n"
            "Приятного аппетита! 🎉",
            reply_markup=main_menu(query.from_user.id)
        )
