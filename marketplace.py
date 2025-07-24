# marketplace.py
import json, os
from datetime import datetime

MARKETPLACE_FILE = "data/marketplace.json"


# ---------- Load & Save ----------
def _load_marketplace():
    if not os.path.exists(MARKETPLACE_FILE):
        return []
    with open(MARKETPLACE_FILE, "r") as f:
        return json.load(f)


def _save_marketplace(listings):
    with open(MARKETPLACE_FILE, "w") as f:
        json.dump(listings, f, indent=2)


# ---------- Add Listing ----------
def list_nft_for_sale(token_id, seller_user, seller_address, price, chain):
    listings = _load_marketplace()

    # Check if already listed
    for listing in listings:
        if listing["token_id"] == token_id:
            raise ValueError("NFT is already listed for sale.")

    listing = {
        "token_id": token_id,
        "seller_user": seller_user,
        "seller_address": seller_address,
        "price": price,
        "chain": chain,
        "listed_at": datetime.utcnow().isoformat()
    }

    listings.append(listing)
    _save_marketplace(listings)
    return listing


# ---------- Remove ----------
def remove_listing(token_id):
    listings = _load_marketplace()
    new_listings = [l for l in listings if l["token_id"] != token_id]
    _save_marketplace(new_listings)


# ---------- Lookup ----------
def get_listing(token_id):
    listings = _load_marketplace()
    for l in listings:
        if l["token_id"] == token_id:
            return l
    return None


def load_marketplace():
    return _load_marketplace()


def get_listings_by_user(seller_user):
    listings = _load_marketplace()
    return [l for l in listings if l["seller_user"] == seller_user]

