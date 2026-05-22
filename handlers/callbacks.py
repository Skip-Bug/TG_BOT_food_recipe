import random

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from config import ADMIN_IDS

from keyboards.keyboards import (
    main_menu,
    admin_menu
)

from services.json_db import (
    load_recipes,
    save_recipes
)


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data


    if data == "admin_panel":

        if query.from_user.id not in ADMIN_IDS:

            await query.edit_message_text(
                "⛔ Нет доступа"
            )

            return

        await query.edit_message_text(
            "👑 Админ-панель",
            reply_markup=admin_menu()
        )


    elif data == "back_to_menu":

        await query.edit_message_text(
            "Главное меню",
            reply_markup=main_menu()
        )


    elif data == "random_recipe":

        recipes = load_recipes()

        if not recipes:

            await query.edit_message_text(
                "📭 Рецептов пока нет"
            )

            return

        recipe = random.choice(recipes)

        ingredients_text = ""

        for ingredient in recipe["ingredients"]:

            ingredients_text += (
                f"• {ingredient['name']} "
                f"- {ingredient['price']}₽\n"
            )

        caption = (

            f"🍽 {recipe['title']}\n\n"

            f"{recipe['description']}\n\n"

            f"💰 Стоимость: "
            f"{recipe['total_price']}₽\n\n"

            f"🥕 Ингредиенты:\n"
            f"{ingredients_text}"
        )

        await query.message.reply_photo(
            photo=recipe["image"],
            caption=caption
        )


    elif data == "recipe_list":

        recipes = load_recipes()

        if not recipes:

            await query.edit_message_text(
                "📭 Рецептов пока нет"
            )

            return

        text = "📋 Рецепты:\n\n"

        for recipe in recipes:

            text += (
                f"{recipe['id']}. "
                f"{recipe['title']} "
                f"({recipe['total_price']}₽)\n"
            )

        await query.edit_message_text(
            text,
            reply_markup=admin_menu()
        )


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

            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="admin_panel"
            )
        ])

        await query.edit_message_text(
            "Выберите рецепт:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    elif data.startswith("delete_"):

        recipe_id = int(data.split("_")[1])

        recipes = load_recipes()

        recipes = [

            recipe
            for recipe in recipes
            if recipe["id"] != recipe_id
        ]

        save_recipes(recipes)

        await query.edit_message_text(
            "✅ Рецепт удалён",
            reply_markup=admin_menu()
        )
```
