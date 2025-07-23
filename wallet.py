# wallet.py

from web3 import Account
import json
import os
import glob

def load_all_wallets():
    all_wallets = []
    files = glob.glob("data/*_wallets.json")
    for path in files:
        user_id = os.path.basename(path).replace("_wallets.json", "")
        with open(path, "r") as f:
            wallets = json.load(f)
            for w in wallets:
                all_wallets.append({
                    "user_id": user_id,
                    "address": w["address"],
                    "nickname": w.get("nickname", "")
                })
    return all_wallets

def get_wallet_file(user_id):
    return f"data/{user_id}_wallets.json"

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

