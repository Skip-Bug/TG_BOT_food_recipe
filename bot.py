import json
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.ext import ConversationHandler

from config import TOKEN, ADMIN_IDS
from keyboards import main_menu, recipe_actions, price_filter_menu, admin_menu, back_button, cancel_button

# ========== РАБОТА С JSON ==========
def load_recipes():
    with open('recipes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_recipes(data):
    with open('recipes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_users():
    with open('users.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(data):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(tg_id):
    """Получить пользователя по tg_id (как строку)"""
    users = load_users()
    for user in users:
        if user['tg_id'] == str(tg_id):
            return user
    return None

def get_user_index(tg_id):
    """Получить индекс пользователя в списке"""
    users = load_users()
    for i, user in enumerate(users):
        if user['tg_id'] == str(tg_id):
            return i
    return None

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
async def start(update: Update, context):
    """Обработчик команды /start"""
    tg_id = str(update.effective_user.id)
    
    # Проверяем, есть ли пользователь в БД
    if get_user(tg_id) is None:
        users = load_users()
        users.append({
            "tg_id": tg_id,
            "subscriber": False,
            "allergy": False,
            "current_recipe": None,
            "recipes_history": [],
            "favorite_recipes": [],
            "price_filter": None
        })
        save_users(users)
    
    await update.message.reply_text(
        f"👋 Привет, {update.effective_user.first_name}!\n\n"
        f"Я FoodPlan бот. Помогу тебе с выбором блюд и планированием бюджета.\n\n"
        f"У тебя есть 3 бесплатных рецепта, затем нужно оформить подписку.",
        reply_markup=main_menu()
    )

async def help_command(update: Update, context):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📖 *Доступные команды:*\n\n"
        "/start - Запустить бота\n"
        "/help - Помощь\n"
        "/menu - Показать главное меню\n\n"
        "*Кнопки меню:*\n"
        "🍽 Случайный рецепт - получить рецепт дня\n"
        "⭐ Избранное - ваши сохранённые рецепты\n"
        "💰 Подписка - оформить платную подписку\n"
        "💸 Фильтр по цене - настроить бюджет\n"
        "👑 Админ-панель - управление рецептами (только для админов)",
        parse_mode='Markdown'
    )

async def menu(update: Update, context):
    """Обработчик команды /menu - показать главное меню"""
    await update.message.reply_text("Главное меню:", reply_markup=main_menu())

# ========== ОБРАБОТЧИКИ КНОПОК ==========
async def button_handler(update: Update, context):
    """Обработчик всех callback_query (нажатий на кнопки)"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "back_to_menu":
        await query.edit_message_text("Главное меню:", reply_markup=main_menu())
    
    elif data == "admin_panel":
        # Проверка на админа
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("⛔ У вас нет доступа к админ-панели.")
            return
        await query.edit_message_text("👑 Админ-панель", reply_markup=admin_menu())
    
    elif data == "set_price_filter":
        tg_id = str(query.from_user.id)
        user = get_user(tg_id)
        current_filter = user.get('price_filter') if user else None
        await query.edit_message_text(
            "💸 *Настройка фильтра по цене*\n\n"
            "Выберите максимальную стоимость блюда:",
            parse_mode='Markdown',
            reply_markup=price_filter_menu(current_filter)
        )
    
    elif data == "subscribe":
        await query.edit_message_text(
            "💰 *Подписка на FoodPlan*\n\n"
            "Стоимость: 199 руб/месяц\n\n"
            "После оплаты вам станут доступны:\n"
            "✅ Безлимитные рецепты\n"
            "✅ Избранное\n"
            "✅ Фильтр по цене\n"
            "✅ Планирование бюджета\n\n"
            "Свяжитесь с @support для оплаты (временно)",
            parse_mode='Markdown',
            reply_markup=back_button()
        )
    
    elif data == "favorites":
        # Пока заглушка
        await query.edit_message_text(
            "⭐ *Избранное*\n\n"
            "Здесь будут сохранённые вами рецепты.\n\n"
            "Чтобы добавить рецепт в избранное, нажмите 🤍 под рецептом.",
            parse_mode='Markdown',
            reply_markup=back_button()
        )
    
    elif data == "random_recipe":
        # Пока заглушка
        await query.edit_message_text(
            "🍽 *Случайный рецепт*\n\n"
            "Здесь будет случайный рецепт из вашей подборки.",
            parse_mode='Markdown',
            reply_markup=back_button()
        )
    
    elif data.startswith("price_"):
        # Обработка выбора фильтра
        tg_id = str(query.from_user.id)
        price_value = data.replace("price_", "")
        
        users = load_users()
        user_index = get_user_index(tg_id)
        
        if user_index is not None:
            if price_value == "clear":
                users[user_index]['price_filter'] = None
                await query.edit_message_text("✅ Фильтр по цене сброшен.", reply_markup=main_menu())
            else:
                users[user_index]['price_filter'] = int(price_value)
                save_users(users)
                await query.edit_message_text(
                    f"✅ Установлен фильтр: до {price_value} руб.",
                    reply_markup=main_menu()
                )
    
    elif data == "cancel":
        await query.edit_message_text("Действие отменено.", reply_markup=main_menu())

# ========== ЗАПУСК ==========
def main():
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu))
    
    # Регистрируем обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    print("Бот запущен")
    application.run_polling()

if __name__ == '__main__':
=======
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