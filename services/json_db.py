import json

def load_recipes():
    try:
        with open("database/recipes.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_recipes(data):
    with open("database/recipes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_users():
    try:
        with open("database/users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_users(data):
    with open("database/users.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user(tg_id):
    users = load_users()
    for u in users:
        if u["tg_id"] == str(tg_id):
            return u
    return None