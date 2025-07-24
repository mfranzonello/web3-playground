# users.py

import os, json

def create_new_user(new_username):
    username = new_username.strip()
    user_dir = f"data/users/{username}"
    os.makedirs(user_dir, exist_ok=True)

    # Initialize empty wallet, balance, and transaction files
    for name in ["wallets", "balances", "transactions"]:
        file_path = f"{user_dir}/{name}.json"
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump([] if name in ['wallets', 'transactions'] else {}, f)

    return username