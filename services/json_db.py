import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
RECIPES_FILE = DB_DIR / "recipes.json"
USERS_FILE = DB_DIR / "users.json"

DB_DIR.mkdir(parents=True, exist_ok=True)


def load_recipes():
    try:
        with open(RECIPES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logger.error("Повреждён recipes.json: %s", e)
        return []


def save_recipes(data):
    with open(RECIPES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logger.error("Повреждён users.json: %s", e)
        return []


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(tg_id):
    users = load_users()
    for user in users:
        if user["tg_id"] == str(tg_id):
            return user
    return None


def register_user(tg_id, is_admin=False):
    if get_user(tg_id) is not None:
        return
    users = load_users()
    users.append({
        "tg_id": str(tg_id),
        "role": "admin" if is_admin else "user",
        "subscriber": is_admin,
        "favorites": [],
        "recipes_viewed": 0
    })
    save_users(users)


def get_role(tg_id):
    user = get_user(str(tg_id))
    if not user:
        return "user"
    return user.get("role", "user")


def increase_views(tg_id):
    users = load_users()
    for user in users:
        if user["tg_id"] == str(tg_id):
            user["recipes_viewed"] += 1
            break
    save_users(users)


def can_view_recipe(tg_id):
    user = get_user(str(tg_id))
    if not user:
        return False
    role = user.get("role", "user")
    if role in ("admin", "subscriber"):
        return True
    return user.get("recipes_viewed", 0) < 3


def set_subscriber(tg_id):
    users = load_users()
    for user in users:
        if user["tg_id"] == str(tg_id):
            user["subscriber"] = True
            user["role"] = "subscriber"
            break
    save_users(users)


def add_to_favorites(tg_id, recipe_id):
    users = load_users()
    for user in users:
        if user["tg_id"] == str(tg_id):
            if recipe_id not in user["favorites"]:
                user["favorites"].append(recipe_id)
            break
    save_users(users)


def remove_from_favorites(tg_id, recipe_id):
    users = load_users()
    for user in users:
        if user["tg_id"] == str(tg_id):
            user["favorites"] = [f for f in user["favorites"] if f != recipe_id]
            break
    save_users(users)


def get_favorites(tg_id):
    user = get_user(str(tg_id))
    if not user:
        return []
    return user.get("favorites", [])
