# nfts.py
import json, os, uuid
from datetime import datetime

CATALOG_PATH = "data/portfolio_catalog.json"
NFT_REGISTRY_PATH = "data/nfts.json"


# ---------- Catalog ----------
def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return []
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


# ---------- Registry Helpers ----------
def _load_registry():
    if not os.path.exists(NFT_REGISTRY_PATH):
        return []
    with open(NFT_REGISTRY_PATH, "r") as f:
        return json.load(f)

def _save_registry(nfts):
    with open(NFT_REGISTRY_PATH, "w") as f:
        json.dump(nfts, f, indent=2)


# ---------- Mint ----------
def mint_nft(asset, chain, owner_user, owner_address):
    """
    asset: dict from catalog (asset_id, title, image_url, description, tags)
    """
    nfts = _load_registry()
    token_id = str(uuid.uuid4())  # simple unique ID; could be numeric
    now = datetime.utcnow().isoformat()

    nft = {
        "token_id": token_id,
        "asset_id": asset["asset_id"],
        "name": asset["title"],
        "image_url": asset["image_url"],
        "description": asset.get("description", ""),
        "chain": chain,
        "owner_user": owner_user,
        "owner_address": owner_address,
        "minted_at": now,
        "history": [
            {"event": "mint", "user": owner_user, "address": owner_address, "ts": now, "chain": chain}
        ]
    }
    nfts.append(nft)
    _save_registry(nfts)
    return nft


# ---------- Transfer ----------
def transfer_nft(token_id, new_owner_user, new_owner_address, chain=None):
    nfts = _load_registry()
    now = datetime.utcnow().isoformat()
    updated = None

    for nft in nfts:
        if nft["token_id"] == token_id:
            prev_user = nft["owner_user"]
            prev_addr = nft["owner_address"]
            nft["owner_user"] = new_owner_user
            nft["owner_address"] = new_owner_address
            if chain:
                nft["chain"] = chain  # optional "bridge" simulation
            nft["history"].append({
                "event": "transfer",
                "from_user": prev_user,
                "from_address": prev_addr,
                "to_user": new_owner_user,
                "to_address": new_owner_address,
                "ts": now,
                "chain": chain or nft["chain"]
            })
            updated = nft
            break

    if updated is None:
        raise ValueError(f"NFT {token_id} not found.")

    _save_registry(nfts)
    return updated


# ---------- Query ----------
def list_nfts_by_owner(owner_user=None, owner_address=None):
    nfts = _load_registry()
    results = []
    for nft in nfts:
        if owner_user and nft["owner_user"] != owner_user:
            continue
        if owner_address and nft["owner_address"] != owner_address:
            continue
        results.append(nft)
    return results

def get_nft(token_id):
    nfts = _load_registry()
    for nft in nfts:
        if nft["token_id"] == token_id:
            return nft
    return None

