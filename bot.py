import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
)

from config import TOKEN, ADMIN_IDS

from services.json_db import (
    load_recipes, save_recipes,
    load_users, save_users, get_user
)

from keyboards.keyboards import main_menu, admin_menu
from states.states import *


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

    if get_user(tg_id) is None:
        users = load_users()
        users.append({
            "tg_id": tg_id,
            "subscriber": False,
            "favorites": [],
            "recipes_viewed": 0
        })
        save_users(users)

    recipes = load_recipes()

    if not recipes:
        return await update.message.reply_text("Нет рецептов")

    recipe = random.choice(recipes)

    text = build_recipe_text(recipe)

    await update.message.reply_photo(
        photo=recipe["photo"],
        caption=text,
        reply_markup=main_menu(update.effective_user.id)
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()
    data = q.data


    if data == "admin_panel":

        if q.from_user.id not in ADMIN_IDS:
            return await q.answer("Нет доступа", show_alert=True)

        return await q.edit_message_text(
            "👑 Админка",
            reply_markup=admin_menu()
        )


    if data == "random_recipe":

        recipes = load_recipes()
        if not recipes:
            return await q.edit_message_text("Нет рецептов")

        recipe = random.choice(recipes)

        text = build_recipe_text(recipe)

        await q.message.reply_photo(
            photo=recipe["photo"],
            caption=text
        )


    if data == "recipe_list":
        recipes = load_recipes()

        if not recipes:
            return await q.edit_message_text("Нет рецептов", reply_markup=admin_menu())

        text = "\n".join([f"{r['id']}. {r['title']}" for r in recipes])

        await q.edit_message_text(text, reply_markup=admin_menu())


    if data == "delete_recipe":

        recipes = load_recipes()

        if not recipes:
            return await q.edit_message_text("Нет рецептов")

        kb = [
            [InlineKeyboardButton(f"❌ {r['title']}", callback_data=f"del_{r['id']}")]
            for r in recipes
        ]

        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_panel")])

        await q.edit_message_text(
            "Удалить рецепт:",
            reply_markup=InlineKeyboardMarkup(kb)
        )


    if data.startswith("del_"):

        rid = int(data.split("_")[1])

        recipes = [r for r in load_recipes() if r["id"] != rid]

        save_recipes(recipes)

        await q.edit_message_text("Удалено", reply_markup=admin_menu())


    if data == "back":
        await q.edit_message_text(
            "Меню",
            reply_markup=main_menu(q.from_user.id)
        )


    if data == "favorites":
        await q.edit_message_text("⭐ Пусто")


    if data == "subscribe":
        await q.edit_message_text("💰 Подписка: 199₽/мес")


async def add_start(update, context):
    q = update.callback_query
    await q.message.reply_text("Название:")
    return ADD_TITLE


async def add_title(update, context):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Описание:")
    return ADD_DESCRIPTION


async def add_desc(update, context):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Ингредиенты (title:amount:price):")
    return ADD_INGREDIENTS


async def add_ing(update, context):

    lines = update.message.text.split("\n")
    ing = []

    for l in lines:
        t, a, p = l.split(":")
        ing.append({"title": t, "amount": a, "price": int(p)})

    context.user_data["ingredients"] = ing

    await update.message.reply_text("Фото:")
    return ADD_IMAGE


async def add_img(update, context):

    photo = update.message.photo[-1]

    recipes = load_recipes()

    new_id = max([r["id"] for r in recipes], default=0) + 1

    recipes.append({
        "id": new_id,
        "title": context.user_data["title"],
        "description": context.user_data["description"],
        "ingredients": context.user_data["ingredients"],
        "allergens": [],
        "photo": photo.file_id
    })

    save_recipes(recipes)

    await update.message.reply_text("Добавлено!")
    return ConversationHandler.END


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(callback))

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_start, pattern="add_recipe")],
        states={
            ADD_TITLE: [MessageHandler(filters.TEXT, add_title)],
            ADD_DESCRIPTION: [MessageHandler(filters.TEXT, add_desc)],
            ADD_INGREDIENTS: [MessageHandler(filters.TEXT, add_ing)],
            ADD_IMAGE: [MessageHandler(filters.PHOTO, add_img)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)

    print("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()