# balances.py

import json
import os

def get_balance_file(user_id):
    return f"data/{user_id}_balances.json"

def load_balances(user_id):
    path = get_balance_file(user_id)
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_balances(user_id, balances):
    path = get_balance_file(user_id)
    with open(path, 'w') as f:
        json.dump(balances, f, indent=2)

def get_wallet_balance(user_id, address):
    balances = load_balances(user_id)
    return balances.get(address, {"USDC": 0})

def update_wallet_balance(user_id, address, amount_delta):
    balances = load_balances(user_id)
    current = balances.get(address, {"USDC": 0})
    current["USDC"] += amount_delta
    balances[address] = current
    save_balances(user_id, balances)

def transfer(user_id, sender_address, recipient_user_id, recipient_address, amount, gas_fee):
    # Subtract from sender
    sender_bal = load_balances(user_id)
    sender = sender_bal.get(sender_address, {"USDC": 0})
    if sender["USDC"] < amount + gas_fee:
        raise ValueError("Insufficient balance")
    sender["USDC"] -= (amount + gas_fee)
    sender_bal[sender_address] = sender
    save_balances(user_id, sender_bal)

    # Add to recipient
    recipient_bal = load_balances(recipient_user_id)
    recipient = recipient_bal.get(recipient_address, {"USDC": 0})
    recipient["USDC"] += amount
    recipient_bal[recipient_address] = recipient
    save_balances(recipient_user_id, recipient_bal)

def off_ramp(user_id, address, amount):
    balances = load_balances(user_id)
    wallet = balances.get(address, {"USDC": 0})
    if wallet["USDC"] < amount:
        raise ValueError("Insufficient USDC to off-ramp")
    wallet["USDC"] -= amount
    balances[address] = wallet
    save_balances(user_id, balances)
