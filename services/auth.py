import json
import os
import config

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def is_authorized(user_id, username=None):
    # Owner is always authorized
    if user_id == config.OWNER_ID or username == config.OWNER_ID:
        return True
    
    users = load_users()
    return str(user_id) in users or (username and username in users)

def add_user(identifier):
    users = load_users()
    if identifier not in users:
        users.append(identifier)
        save_users(users)
        return True
    return False

def remove_user(identifier):
    users = load_users()
    if identifier in users:
        users.remove(identifier)
        save_users(users)
        return True
    return False

def get_users():
    return load_users()
