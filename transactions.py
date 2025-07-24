# transactions.py

import json
import os
from datetime import datetime

def get_tx_file(user_id):
    return f"data/users/{user_id}/transactions.json"

def load_transactions(user_id):
    path = get_tx_file(user_id)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_transaction(user_id, tx):
    txs = load_transactions(user_id)
    txs.append(tx)
    with open(get_tx_file(user_id), "w") as f:
        json.dump(txs, f, indent=2)

