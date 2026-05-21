from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler
)

from services.json_db import (
    load_recipes,
    save_recipes
)

from states.recipe_states import *


async def add_recipe_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

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
        "Формат:\n"
        "Сыр:200\n"
        "Тесто:100"
    )

    return ADD_INGREDIENTS


async def add_ingredients(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    lines = update.message.text.split("\n")

    ingredients = []

    total_price = 0

    for line in lines:

        name, price = line.split(":")

        ingredients.append({

            "name": name.strip(),

            "price": int(price.strip())
        })

        total_price += int(price.strip())

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

    recipe = {

        "id": len(recipes) + 1,

        "title": context.user_data["title"],

        "description": context.user_data["description"],

        "ingredients": context.user_data["ingredients"],

        "total_price": context.user_data["total_price"],

        "image": photo.file_id
    }

    recipes.append(recipe)

    save_recipes(recipes)

    await update.message.reply_text(
        "✅ Рецепт добавлен!"
    )

    return ConversationHandler.END


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "❌ Добавление отменено"
    )

    return ConversationHandler.END
