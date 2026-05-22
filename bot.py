import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
)

from config import TOKEN, ADMIN_IDS
from services.json_db import load_recipes, save_recipes, load_users, save_users, get_user
from keyboards.keyboards import (
    main_menu, admin_menu, cancel_menu,
    recipe_menu_free, recipe_menu_premium,
    price_filter_menu,
)
from states.states import ADD_TITLE, ADD_DESCRIPTION, ADD_INGREDIENTS, ADD_IMAGE

# Номер телефона для оплаты
PAYMENT_PHONE = "+7 900 000 00 00"
PAYMENT_AMOUNT = "199₽/мес"


# ──────────────────────────── helpers ────────────────────────────

def get_or_create_user(tg_id: str):
    user = get_user(tg_id)
    if user is None:
        users = load_users()
        user = {
            "tg_id": tg_id,
            "subscriber": False,
            "favorites": [],
            "recipes_viewed": 0,
            "price_filter": None,
            "awaiting_payment": False,
        }
        users.append(user)
        save_users(users)
    return user


def update_user(tg_id: str, **fields):
    users = load_users()
    for u in users:
        if u["tg_id"] == tg_id:
            u.update(fields)
            save_users(users)
            return u
    return None


def is_premium(user) -> bool:
    return user.get("subscriber", False) or int(user["tg_id"]) in ADMIN_IDS


def build_recipe_text(recipe) -> str:
    ingredients = recipe.get("ingredients", [])
    ing_text = ""
    total = recipe.get("total_price", 0) or sum(i.get("price", 0) for i in ingredients)

    for i in ingredients:
        name   = i.get("title") or i.get("name", "")
        weight = i.get("weight")
        price  = i.get("price", 0)
        line   = f"• {name}"
        if weight:
            line += f" — {weight}г"
        line += f" — {price}₽\n"
        ing_text += line

    return (
        f"🍽 *{recipe['title']}*\n\n"
        f"{recipe['description']}\n\n"
        f"💰 Стоимость: {total}₽\n\n"
        f"🥕 Ингредиенты:\n{ing_text}"
    )


# ──────────────────────────── /start ─────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = str(update.effective_user.id)
    user  = get_or_create_user(tg_id)
    name  = update.effective_user.first_name
    premium = is_premium(user)
    viewed  = user.get("recipes_viewed", 0)

    if premium:
        text = (
            f"👋 Привет, {name}!\n\n"
            f"Я FoodPlan бот. Помогу тебе с выбором блюд и планированием бюджета.\n\n"
            f"⭐ У тебя активна премиум-подписка."
        )
    else:
        left = max(0, 3 - viewed)
        text = (
            f"👋 Привет, {name}!\n\n"
            f"Я FoodPlan бот. Помогу тебе с выбором блюд и планированием бюджета.\n\n"
            f"У тебя есть {left} бесплатных рецепт(а), затем нужно оформить подписку."
        )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(premium, viewed)
    )


# ──────────────────────────── /admin ─────────────────────────────

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет доступа.")
        return
    await update.message.reply_text("👑 Админ-панель", reply_markup=admin_menu())


# ──────────────────── обработчик скриншотов оплаты ───────────────

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловит фото от пользователей, ожидающих подтверждения подписки."""
    tg_id = str(update.effective_user.id)
    user  = get_user(tg_id)

    if not user or not user.get("awaiting_payment"):
        return  # не наш кейс

    # Снять флаг ожидания
    update_user(tg_id, awaiting_payment=False)

    photo     = update.message.photo[-1]
    user_name = update.effective_user.full_name
    user_link = f"@{update.effective_user.username}" if update.effective_user.username else f"ID {tg_id}"

    # Уведомить всех админов со скриншотом и кнопкой одобрения
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=(
                    f"💳 Запрос на подписку\n\n"
                    f"Пользователь: {user_name} ({user_link})\n"
                    f"ID: {tg_id}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        f"✅ Одобрить подписку",
                        callback_data=f"approve_sub_{tg_id}"
                    )],
                    [InlineKeyboardButton(
                        f"❌ Отклонить",
                        callback_data=f"reject_sub_{tg_id}"
                    )],
                ])
            )
        except Exception:
            pass

    await update.message.reply_text(
        "✅ Скриншот отправлен на проверку.\n\n"
        "Как только администратор подтвердит оплату, вам откроется полный доступ."
    )


# ──────────────────────────── callbacks ──────────────────────────

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    data = q.data
    tg_id = str(q.from_user.id)

    # ── Главное меню ──
    if data == "back_to_menu":
        user    = get_user(tg_id)
        premium = is_premium(user) if user else False
        viewed  = user.get("recipes_viewed", 0) if user else 0
        await q.edit_message_text("Главное меню:", reply_markup=main_menu(premium, viewed))

    # ── Случайный рецепт ──
    elif data == "random_recipe":
        user    = get_or_create_user(tg_id)
        premium = is_premium(user)
        viewed  = user.get("recipes_viewed", 0)

        # Лимит для бесплатных
        if not premium and viewed >= 3:
            await q.edit_message_text(
                "🔒 Вы использовали все 3 бесплатных рецепта.\n\n"
                "Оформите подписку чтобы получить безлимитный доступ.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Оформить подписку", callback_data="subscribe")]
                ])
            )
            return

        price_filter = user.get("price_filter") if premium else None
        fav_ids      = user.get("favorites", []) if premium else []

        recipes = load_recipes()
        if price_filter:
            filtered = [
                r for r in recipes
                if r.get("total_price", sum(i.get("price", 0) for i in r.get("ingredients", []))) <= price_filter
            ]
            recipes = filtered if filtered else recipes

        if not recipes:
            await q.edit_message_text("📭 Рецептов пока нет.", reply_markup=main_menu(premium, viewed))
            return

        recipe = random.choice(recipes)
        text   = build_recipe_text(recipe)

        # Увеличить счётчик просмотров
        update_user(tg_id, recipes_viewed=viewed + 1)
        viewed += 1

        if premium:
            in_fav = recipe["id"] in fav_ids
            markup = recipe_menu_premium(recipe["id"], in_favorites=in_fav)
        else:
            markup = recipe_menu_free(recipe["id"])
            if viewed >= 3:
                # Последний бесплатный — добавить подсказку
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Ещё рецепт (нужна подписка)", callback_data="subscribe")],
                    [InlineKeyboardButton("💰 Оформить подписку",           callback_data="subscribe")],
                    [InlineKeyboardButton("⬅️ Назад",                       callback_data="back_to_menu")],
                ])

        image = recipe.get("image")
        if image:
            await q.message.reply_photo(photo=image, caption=text, parse_mode="Markdown", reply_markup=markup)
        else:
            await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)

    # ── Избранное (только премиум) ──
    elif data == "favorites":
        user = get_user(tg_id)
        if not is_premium(user):
            await q.answer("⭐ Доступно только для премиум-пользователей.", show_alert=True)
            return
        await _show_favorites(q, user)

    elif data.startswith("show_recipe_"):
        recipe_id = int(data.split("_")[2])
        user      = get_user(tg_id)
        fav_ids   = user.get("favorites", []) if user else []
        recipe    = next((r for r in load_recipes() if r["id"] == recipe_id), None)
        if not recipe:
            await q.edit_message_text("Рецепт не найден.", reply_markup=main_menu(is_premium(user), user.get("recipes_viewed", 0)))
            return
        in_fav = recipe_id in fav_ids
        kb = [
            [InlineKeyboardButton(
                "❤️ Убрать из избранного" if in_fav else "🤍 В избранное",
                callback_data=f"unfav_{recipe_id}" if in_fav else f"fav_{recipe_id}"
            )],
            [InlineKeyboardButton("⬅️ К избранному", callback_data="favorites")],
        ]
        await q.edit_message_text(build_recipe_text(recipe), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("fav_"):
        recipe_id = int(data.split("_")[1])
        user      = get_user(tg_id)
        if not is_premium(user):
            await q.answer("⭐ Доступно только для премиум-пользователей.", show_alert=True)
            return
        if recipe_id not in user.get("favorites", []):
            update_user(tg_id, favorites=user.get("favorites", []) + [recipe_id])
        recipe = next((r for r in load_recipes() if r["id"] == recipe_id), None)
        if recipe:
            await q.edit_message_text(
                build_recipe_text(recipe), parse_mode="Markdown",
                reply_markup=recipe_menu_premium(recipe_id, in_favorites=True)
            )

    elif data.startswith("unfav_"):
        recipe_id = int(data.split("_")[1])
        user      = get_user(tg_id)
        new_favs  = [f for f in user.get("favorites", []) if f != recipe_id]
        update_user(tg_id, favorites=new_favs)
        recipe    = next((r for r in load_recipes() if r["id"] == recipe_id), None)
        if recipe and q.message.caption is None:
            # Пришли из списка избранного
            user2 = get_user(tg_id)
            await _show_favorites(q, user2)
        elif recipe:
            await q.edit_message_text(
                build_recipe_text(recipe), parse_mode="Markdown",
                reply_markup=recipe_menu_premium(recipe_id, in_favorites=False)
            )

    # ── Подписка ──
    elif data == "subscribe":
        await q.edit_message_text(
            f"💰 *Оформление подписки FoodPlan*\n\n"
            f"Стоимость: *{PAYMENT_AMOUNT}*\n\n"
            f"После оплаты вам станут доступны:\n"
            f"✅ Безлимитные рецепты\n"
            f"✅ Избранное\n"
            f"✅ Фильтр по цене\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Переведите оплату на номер:\n"
            f"📱 *{PAYMENT_PHONE}*\n\n"
            f"После оплаты нажмите кнопку ниже и пришлите скриншот чека.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Отправить скриншот оплаты", callback_data="send_screenshot")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")],
            ])
        )

    elif data == "send_screenshot":
        update_user(tg_id, awaiting_payment=True)
        await q.edit_message_text(
            "📸 Пришлите скриншот подтверждения оплаты.\n\n"
            "Как только администратор проверит платёж, вам откроется полный доступ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_payment")]
            ])
        )

    elif data == "cancel_payment":
        update_user(tg_id, awaiting_payment=False)
        user   = get_user(tg_id)
        viewed = user.get("recipes_viewed", 0)
        await q.edit_message_text("Главное меню:", reply_markup=main_menu(is_premium(user), viewed))

    elif data == "sub_info":
        await q.answer("⭐ Ваша подписка активна!", show_alert=True)

    # ── Одобрение подписки (только для админов) ──
    elif data.startswith("approve_sub_"):
        if q.from_user.id not in ADMIN_IDS:
            await q.answer("⛔ Нет доступа.", show_alert=True)
            return
        target_tg_id = data.replace("approve_sub_", "")
        update_user(target_tg_id, subscriber=True, awaiting_payment=False)
        await q.edit_message_caption(
            caption=q.message.caption + "\n\n✅ Одобрено",
            reply_markup=None
        )
        # Уведомить пользователя
        try:
            target_user = get_user(target_tg_id)
            await context.bot.send_message(
                chat_id=int(target_tg_id),
                text=(
                    "🎉 Ваша подписка подтверждена!\n\n"
                    "Теперь вам доступны:\n"
                    "✅ Безлимитные рецепты\n"
                    "✅ Избранное\n"
                    "✅ Фильтр по цене\n\n"
                    "Нажмите /start чтобы открыть меню."
                )
            )
        except Exception:
            pass

    elif data.startswith("reject_sub_"):
        if q.from_user.id not in ADMIN_IDS:
            await q.answer("⛔ Нет доступа.", show_alert=True)
            return
        target_tg_id = data.replace("reject_sub_", "")
        update_user(target_tg_id, awaiting_payment=False)
        await q.edit_message_caption(
            caption=q.message.caption + "\n\n❌ Отклонено",
            reply_markup=None
        )
        try:
            await context.bot.send_message(
                chat_id=int(target_tg_id),
                text=(
                    "❌ К сожалению, ваш платёж не был подтверждён.\n\n"
                    "Если произошла ошибка, свяжитесь с поддержкой."
                )
            )
        except Exception:
            pass

    # ── Фильтр по цене ──
    elif data == "set_price_filter":
        user = get_user(tg_id)
        if not is_premium(user):
            await q.answer("💸 Доступно только для премиум-пользователей.", show_alert=True)
            return
        current = user.get("price_filter")
        status  = f"Текущий фильтр: до {current}₽" if current else "Фильтр не установлен"
        await q.edit_message_text(
            f"💸 *Фильтр по цене*\n\n{status}\n\nВыберите максимальную стоимость блюда:",
            parse_mode="Markdown",
            reply_markup=price_filter_menu()
        )

    elif data.startswith("price_"):
        val = data.replace("price_", "")
        update_user(tg_id, price_filter=None if val == "clear" else int(val))
        msg = "✅ Фильтр сброшен." if val == "clear" else f"✅ Установлен фильтр: до {val}₽."
        user   = get_user(tg_id)
        viewed = user.get("recipes_viewed", 0)
        await q.edit_message_text(msg, reply_markup=main_menu(is_premium(user), viewed))

    # ── Админ: список / удаление ──
    elif data == "recipe_list":
        recipes = load_recipes()
        if not recipes:
            await q.edit_message_text("📭 Рецептов пока нет.", reply_markup=admin_menu())
            return
        text = "📋 *Рецепты:*\n\n"
        for r in recipes:
            total = r.get("total_price", sum(i.get("price", 0) for i in r.get("ingredients", [])))
            text += f"{r['id']}. {r['title']} — {total}₽\n"
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=admin_menu())

    elif data == "delete_recipe":
        recipes = load_recipes()
        if not recipes:
            await q.edit_message_text("📭 Рецептов нет.", reply_markup=admin_menu())
            return
        kb = [
            [InlineKeyboardButton(f"❌ {r['title']}", callback_data=f"delete_{r['id']}")]
            for r in recipes
        ]
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_admin")])
        await q.edit_message_text("Выберите рецепт для удаления:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("delete_"):
        rid     = int(data.split("_")[1])
        recipes = [r for r in load_recipes() if r["id"] != rid]
        save_recipes(recipes)
        await q.edit_message_text("✅ Рецепт удалён.", reply_markup=admin_menu())

    elif data == "back_admin":
        await q.edit_message_text("👑 Админ-панель", reply_markup=admin_menu())

    elif data == "cancel_add":
        context.user_data.clear()
        await q.edit_message_text("❌ Добавление отменено.", reply_markup=admin_menu())
        return ConversationHandler.END


async def _show_favorites(q, user):
    fav_ids     = user.get("favorites", [])
    if not fav_ids:
        await q.edit_message_text(
            "⭐ Избранное пустое.\n\nДобавляй рецепты кнопкой 🤍 под рецептом.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
            ])
        )
        return
    recipes     = load_recipes()
    fav_recipes = [r for r in recipes if r["id"] in fav_ids]
    kb = [
        [InlineKeyboardButton(f"🍽 {r['title']}", callback_data=f"show_recipe_{r['id']}")]
        for r in fav_recipes
    ]
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])
    await q.edit_message_text(
        "⭐ *Избранное:*\n\nВыберите рецепт чтобы открыть:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ──────────────────── добавление рецепта (ConvHandler) ───────────

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        "Введите название рецепта:\n\n_(или нажмите кнопку ниже чтобы отменить)_",
        parse_mode="Markdown",
        reply_markup=cancel_menu()
    )
    return ADD_TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание рецепта:", reply_markup=cancel_menu())
    return ADD_DESCRIPTION


async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text(
        "Введите ингредиенты, каждый с новой строки:\n\n"
        "Формат: *Название:граммы:цена\\_за\\_кг*\n\n"
        "Пример:\n`Куриное филе:300:450`\n`Сливки:200:180`\n\n"
        "_Цена = граммы ÷ 1000 × цена за кг_",
        parse_mode="Markdown",
        reply_markup=cancel_menu()
    )
    return ADD_INGREDIENTS


async def add_ing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines       = update.message.text.strip().split("\n")
    ingredients = []
    total       = 0
    errors      = []

    for line in lines:
        parts = [p.strip() for p in line.split(":")]
        if len(parts) == 3:
            name, weight, ppkg = parts[0], int(parts[1]), int(parts[2])
            price = round(weight / 1000 * ppkg)
            ingredients.append({"name": name, "weight": weight, "price_per_kg": ppkg, "price": price})
            total += price
        elif len(parts) == 2:
            name, price = parts[0], int(parts[1])
            ingredients.append({"name": name, "price": price})
            total += price
        else:
            errors.append(line)

    if errors:
        await update.message.reply_text(
            f"⚠️ Не удалось разобрать строки:\n" + "\n".join(errors) +
            "\n\nПопробуйте снова. Формат: Название:граммы:цена_за_кг",
            reply_markup=cancel_menu()
        )
        return ADD_INGREDIENTS

    context.user_data["ingredients"] = ingredients
    context.user_data["total_price"] = total

    preview = "\n".join(
        f"• {i['name']}{' — ' + str(i['weight']) + 'г' if i.get('weight') else ''} — {i['price']}₽"
        for i in ingredients
    )
    await update.message.reply_text(
        f"✅ Ингредиенты:\n\n{preview}\n\n💰 Итого: {total}₽\n\nОтправьте фото блюда:",
        reply_markup=cancel_menu()
    )
    return ADD_IMAGE


async def add_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo   = update.message.photo[-1]
    recipes = load_recipes()
    new_id  = max([r["id"] for r in recipes], default=0) + 1
    recipes.append({
        "id":          new_id,
        "title":       context.user_data["title"],
        "description": context.user_data["description"],
        "ingredients": context.user_data["ingredients"],
        "total_price": context.user_data["total_price"],
        "image":       photo.file_id,
    })
    save_recipes(recipes)
    context.user_data.clear()
    await update.message.reply_text("✅ Рецепт добавлен!", reply_markup=admin_menu())
    return ConversationHandler.END


async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление отменено.", reply_markup=admin_menu())
    return ConversationHandler.END


async def cancel_add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    await q.edit_message_text("❌ Добавление отменено.", reply_markup=admin_menu())
    return ConversationHandler.END


# ──────────────────────────── main ───────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_start, pattern="^add_recipe$")],
        states={
            ADD_TITLE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ing)],
            ADD_IMAGE: [
                MessageHandler(filters.PHOTO, add_img),
                CallbackQueryHandler(cancel_add_button, pattern="^cancel_add$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conv),
            CallbackQueryHandler(cancel_add_button, pattern="^cancel_add$"),
        ],
        per_message=False
    )

    app.add_handler(conv)
    # Скриншоты оплаты — вне ConversationHandler
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    app.add_handler(CallbackQueryHandler(callback))

    print("Bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
