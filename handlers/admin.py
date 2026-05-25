from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler
)
from services.json_db import (
    load_recipes,
    save_recipes
)
from states.states import *


async def add_recipe_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Введите название рецепта:"
    )
    return ADD_TITLE


async def add_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["title"] = update.message.text
    await update.message.reply_text(
        "Введите описание:"
    )
    return ADD_DESCRIPTION


async def add_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["description"] = update.message.text
    await update.message.reply_text(
        "Введите ингредиенты:\n\n"
        "Формат (название:количество:цена):\n"
        "Сыр:200г:150\n"
        "Тесто:100г:50"
    )
    return ADD_INGREDIENTS


async def add_ingredients(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    lines = update.message.text.strip().split("\n")
    ingredients = []
    total_price = 0

    for line in lines:
        parts = line.split(":")

        if len(parts) != 3:
            await update.message.reply_text(
                f"❌ Неверный формат: `{line}`\n"
                "Используй формат: название:количество:цена\n"
                "Попробуй снова:",
                parse_mode="Markdown"
            )
            return ADD_INGREDIENTS

        name, amount, price = parts

        try:
            price_int = int(price.strip())
        except ValueError:
            await update.message.reply_text(
                f"❌ Цена должна быть числом, получено: `{price}`\n"
                "Попробуй снова:",
                parse_mode="Markdown"
            )
            return ADD_INGREDIENTS

        ingredients.append({
            "title": name.strip(),
            "amount": amount.strip(),
            "price": price_int
        })
        total_price += price_int

    context.user_data["ingredients"] = ingredients
    context.user_data["total_price"] = total_price

    await update.message.reply_text(
        "Отправьте фото блюда:"
    )
    return ADD_IMAGE


async def add_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    photo = update.message.photo[-1]
    recipes = load_recipes()

    new_id = max((recipe["id"] for recipe in recipes), default=0) + 1

    recipe = {
        "id": new_id,
        "title": context.user_data["title"],
        "description": context.user_data["description"],
        "ingredients": context.user_data["ingredients"],
        "total_price": context.user_data["total_price"],
        "allergens": [],
        "photo": photo.file_id
    }

    recipes.append(recipe)
    save_recipes(recipes)

    await update.message.reply_text(
        "✅ Рецепт добавлен!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить ещё", callback_data="add_recipe")],
            [InlineKeyboardButton("📋 Список рецептов", callback_data="recipe_list")],
            [InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]
        ])
    )
    return ConversationHandler.END


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "❌ Добавление отменено",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]
        ])
    )
    return ConversationHandler.END
