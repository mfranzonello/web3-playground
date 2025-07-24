# wallet.py

from web3 import Account
import json
import os
import glob

def get_wallet_file(user_id):
    return f"data/users/{user_id}/wallets.json"

def ensure_user_dir(user_id):
    path = os.path.dirname(get_wallet_file(user_id))
    os.makedirs(path, exist_ok=True)

# ----------- User Utilities -----------

def list_users():
    """Return all user IDs based on subdirectories in /data/users/"""
    user_root = "data/users"
    if not os.path.exists(user_root):
        return []
    return sorted([name for name in os.listdir(user_root) if os.path.isdir(os.path.join(user_root, name))])

# ----------- Wallet Operations -----------

def load_all_wallets():
    """Load all wallets from all user folders"""
    all_wallets = []
    user_root = "data/users"
    if not os.path.exists(user_root):
        return []

    for user_id in os.listdir(user_root):
        wallet_file = os.path.join(user_root, user_id, "wallets.json")
        if not os.path.exists(wallet_file):
            continue
        with open(wallet_file, "r") as f:
            try:
                wallets = json.load(f)
                for w in wallets:
                    all_wallets.append({
                        "user_id": user_id,
                        "address": w["address"],
                        "nickname": w.get("nickname", "")
                    })
            except json.JSONDecodeError:
                pass  # Could add logging here
    return all_wallets

def create_wallet(user_id, nickname=None):
    acct = Account.create()
    wallet = {
        "address": acct.address,
        "private_key": acct.key.hex(),
        "nickname": nickname or ""
    }
    save_wallet(user_id, wallet)
    return wallet

def save_wallet(user_id, wallet):
    wallet_file = get_wallet_file(user_id)
    if not os.path.exists(wallet_file):
        with open(wallet_file, 'w') as f:
            json.dump([wallet], f, indent=2)
    else:
        with open(wallet_file, 'r+') as f:
            data = json.load(f)
            data.append(wallet)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

def get_wallets(user_id):
    wallet_file = get_wallet_file(user_id)
    if not os.path.exists(wallet_file):
        return []
    with open(wallet_file, 'r') as f:
        wallets = json.load(f)
    # Ensure backward compatibility
    for wallet in wallets:
        if 'nickname' not in wallet:
            wallet['nickname'] = ""
    return wallets

def update_wallet_nickname(user_id, address, new_nickname):
    wallet_file = get_wallet_file(user_id)
    if not os.path.exists(wallet_file):
        return
    with open(wallet_file, 'r+') as f:
        wallets = json.load(f)
        for wallet in wallets:
            if wallet['address'] == address:
                wallet['nickname'] = new_nickname
                break
        f.seek(0)
        json.dump(wallets, f, indent=2)
        f.truncate()

def delete_wallet(user_id, address):
    wallet_file = get_wallet_file(user_id)
    if not os.path.exists(wallet_file):
        return
    with open(wallet_file, 'r+') as f:
        wallets = json.load(f)
        wallets = [w for w in wallets if w['address'] != address]
        f.seek(0)
        json.dump(wallets, f, indent=2)
        f.truncate()

