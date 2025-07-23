from datetime import datetime

import streamlit as st

from wallet import create_wallet, get_wallets, load_all_wallets
from balances import get_wallet_balance, update_wallet_balance, transfer, off_ramp
from chains import CHAINS, DEFAULT_CHAIN
from transactions import save_transaction, load_transactions
from nfts import load_catalog, mint_nft, list_nfts_by_owner, transfer_nft, burn_nft
from calculator import calculate_gas_fee



st.set_page_config(page_title="SimChain", layout="wide")

# Initialize session state for active wallet and chain
if "active_wallet_address" not in st.session_state:
    st.session_state.active_wallet_address = None

if "active_chain" not in st.session_state:
    st.session_state.active_chain = DEFAULT_CHAIN

# ---- User Login UI ----
st.sidebar.header("👤 User Login")

from wallet import list_users

existing_users = list_users()
new_user = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

login_mode = st.sidebar.radio("Select login method", ["Choose existing user", "Create new user"])

if login_mode == "Choose existing user":
    if existing_users:
        selected_user = st.sidebar.selectbox("Select a user", existing_users)
        if st.sidebar.button("Login as selected user"):
            st.session_state.user_id = selected_user
            st.rerun()
    else:
        st.sidebar.info("No users yet. Create one below.")
elif login_mode == "Create new user":
    new_username = st.sidebar.text_input("Choose a username")
    if st.sidebar.button("Create & Login"):
        if new_username in existing_users:
            st.sidebar.error("Username already exists.")
        elif not new_username.strip():
            st.sidebar.error("Username can't be empty.")
        else:
            st.session_state.user_id = new_username.strip()
            st.rerun()

user_id = st.session_state.get("user_id", "")
if not user_id:
    st.title("🔗 SimChain – Web3 Simulation Dashboard")
    st.warning("Please log in or create a user to get started.")
    st.stop()



# ---- Wallet Creation ----
st.header(f"🪪 Wallet Manager for `{user_id}`")

nickname = st.text_input("Optional: Name this wallet (e.g., Chase, Savings, Testnet)")
if st.button("➕ Create New Wallet"):
    new_wallet = create_wallet(user_id=user_id, nickname=nickname)
    st.success(f"Created wallet: {nickname or new_wallet['address']}")
    st.session_state.active_wallet_address = new_wallet["address"]
    st.rerun()

# ---- Load Wallets ----
wallets = get_wallets(user_id=user_id)
if not wallets:
    st.info("No wallets created yet.")
    st.stop()

# ---- Wallet Selector ----
st.subheader("📜 Your Wallets")

# Build label for each wallet
labels = [
    f"{w['nickname']} ({w['address'][:6]}…{w['address'][-4:]})" if w['nickname']
    else w['address']
    for w in wallets
]

# Find the default index from session state
default_index = 0
if st.session_state.active_wallet_address:
    for i, w in enumerate(wallets):
        if w['address'] == st.session_state.active_wallet_address:
            default_index = i
            break

selected_label = st.selectbox("🎯 Choose active wallet", labels, index=default_index)
selected_index = labels.index(selected_label)
st.session_state.active_wallet_address = wallets[selected_index]["address"]

active_wallet = wallets[selected_index]

st.success(f"Active wallet: {active_wallet['nickname'] or active_wallet['address']}")

# ---- Wallet Balance ----
st.subheader("💰 Wallet Balance")

balance = get_wallet_balance(user_id, active_wallet["address"])
st.metric(label="USDC", value=f'{balance["USDC"]:.2f}')

if st.button("🔼 Simulate On-Ramp (Deposit $500 USDC)"):
    update_wallet_balance(user_id, active_wallet["address"], 500)

    save_transaction(user_id, {
    "type": "onramp",
    "wallet": active_wallet["address"],
    "amount": 500,
    "chain": st.session_state.active_chain,
    "timestamp": datetime.utcnow().isoformat(),
    "gas_fee": 0,
    "direction": "in"
    })

    st.success("Deposited $500 USDC!")
    st.rerun()

# ---- List All Wallets ----
all_wallets = load_all_wallets()
recipient_options = [
    f"{w['nickname']} ({w['address'][:6]}…{w['address'][-4:]}) — @{w['user_id']}"
    if w['nickname'] else f"{w['address']} — @{w['user_id']}"
    for w in all_wallets if w['address'] != active_wallet["address"]
]
recipient_wallets = [w for w in all_wallets if w['address'] != active_wallet["address"]]

# ---- NFTs Owned ----
st.subheader("🖼 NFTs Owned by This Wallet")

owned_nfts = list_nfts_by_owner(owner_address=active_wallet["address"])
if owned_nfts:
    for nft in owned_nfts:
        with st.expander(f"{nft['name']} (Token {nft['token_id'][:8]}…)"):
            st.image(nft["image_url"], caption=nft["name"], use_container_width=True)
            st.write(nft["description"])
            st.text(f"Token ID: {nft['token_id']}")

    st.markdown("---")
    st.subheader("🔁 Transfer NFT")

    nft_options = [f"{nft['name']} (Token {nft['token_id'][:8]}…)" for nft in owned_nfts]
    selected_nft_label = st.selectbox("Select NFT to transfer", nft_options)
    selected_nft = owned_nfts[nft_options.index(selected_nft_label)]

    # Pick recipient wallet
    recipient_nft_options = [
        f"{w['nickname']} ({w['address'][:6]}…{w['address'][-4:]}) — @{w['user_id']}"
        if w['nickname'] else f"{w['address']} — @{w['user_id']}"
        for w in all_wallets if w['address'] != active_wallet["address"]
    ]
    recipient_wallets = [w for w in all_wallets if w['address'] != active_wallet["address"]]

    if recipient_nft_options:
        recipient_choice = st.selectbox("Transfer NFT to", recipient_nft_options)
        recipient_wallet = recipient_wallets[recipient_nft_options.index(recipient_choice)]

        if st.button("Confirm NFT Transfer"):
            gas_fee = calculate_gas_fee(CHAINS[st.session_state.active_chain], "medium")
            if balance["USDC"] < gas_fee:
                st.error("Not enough USDC to cover gas.")
            else:
                update_wallet_balance(user_id, active_wallet["address"], -gas_fee)
                transfer_nft(
                    token_id=selected_nft["token_id"],
                    ##sender_user_id=user_id,
                    ##sender_address=active_wallet["address"],
                    ##recipient_user_id=recipient_wallet["user_id"],
                    ##recipient_address=recipient_wallet["address"]
                    new_owner_user=recipient_wallet["user_id"],
                    new_owner_address=recipient_wallet["address"]
                )

                save_transaction(user_id, {
                    "type": "nft_transfer",
                    "wallet": active_wallet["address"],
                    "token_id": selected_nft["token_id"],
                    "recipient": recipient_wallet["address"],
                    "chain": st.session_state.active_chain,
                    "timestamp": datetime.utcnow().isoformat(),
                    "gas_fee": gas_fee,
                    "direction": "out"
                })
                save_transaction(recipient_wallet["user_id"], {
                    "type": "nft_received",
                    "wallet": recipient_wallet["address"],
                    "token_id": selected_nft["token_id"],
                    "sender": active_wallet["address"],
                    "chain": st.session_state.active_chain,
                    "timestamp": datetime.utcnow().isoformat(),
                    "gas_fee": 0,
                    "direction": "in"
                })

                st.success("NFT transferred successfully!")
                st.rerun()
    else:
        st.info("No other wallets to transfer to.")


    st.markdown("---")
    st.subheader("🔥 Burn NFT")

    burn_nft_label = st.selectbox("Select NFT to burn", nft_options, key="burn_select")
    nft_to_burn = owned_nfts[nft_options.index(burn_nft_label)]

    if st.button("Confirm Burn"):
        gas_fee = calculate_gas_fee(CHAINS[st.session_state.active_chain], "medium")
        if balance["USDC"] < gas_fee:
            st.error("Not enough USDC to cover gas.")
        else:
            update_wallet_balance(user_id, active_wallet["address"], -gas_fee)
            burn_nft(nft_to_burn["token_id"])

            save_transaction(user_id, {
                "type": "nft_burn",
                "wallet": active_wallet["address"],
                "token_id": nft_to_burn["token_id"],
                "chain": st.session_state.active_chain,
                "timestamp": datetime.utcnow().isoformat(),
                "gas_fee": gas_fee,
                "direction": "out"
            })

            st.success("NFT burned successfully.")
            st.rerun()

else:
    st.info("This wallet doesn't own any NFTs yet.")



# ---- Transfer Funds ----
st.subheader("🔁 Simulate USDC Transfer")

if recipient_options:
    recipient_choice = st.selectbox("Choose recipient wallet", recipient_options)
    selected = recipient_wallets[recipient_options.index(recipient_choice)]
    recipient_address = selected["address"]
    recipient_user_id = selected["user_id"]

    amount_to_send = st.number_input("Amount to send", min_value=0.0, step=1.0)

    if st.button("Send USDC"):
        try:
            gas_fee = CHAINS[st.session_state.active_chain]["gas_fee"]
            transfer(user_id, active_wallet["address"], recipient_user_id, recipient_address, amount_to_send, gas_fee)

            timestamp = datetime.utcnow().isoformat()

            save_transaction(user_id, {
                "type": "transfer_sent",
                "wallet": active_wallet["address"],
                "amount": amount_to_send,
                "recipient": recipient_address,
                "chain": st.session_state.active_chain,
                "timestamp": timestamp,
                "gas_fee": gas_fee,
                "direction": "out"
            })

            save_transaction(recipient_user_id, {
                "type": "transfer_received",
                "wallet": recipient_address,
                "amount": amount_to_send,
                "sender": active_wallet["address"],
                "chain": st.session_state.active_chain,
                "timestamp": timestamp,
                "gas_fee": 0,
                "direction": "in"
            })

            st.success(f"Sent {amount_to_send:.2f} USDC to @{recipient_user_id}")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
else:
    st.info("No wallets available to send to.")


# ---- Off-Ramp to Fiat ----
st.subheader("💸 Off-Ramp to Fiat")

amount_to_withdraw = st.number_input("Amount to off-ramp", min_value=0.0, step=1.0, key="offramp_input")

if st.button("Withdraw"):
    try:
        off_ramp(user_id, active_wallet["address"], amount_to_withdraw)

        save_transaction(user_id, {
        "type": "offramp",
        "wallet": active_wallet["address"],
        "amount": amount_to_withdraw,
        "chain": st.session_state.active_chain,
        "timestamp": datetime.utcnow().isoformat(),
        "gas_fee": 0,
        "direction": "out"
        })

        st.success(f"Withdrew {amount_to_withdraw:.2f} USDC to fiat.")
        st.rerun()
    except ValueError as e:
        st.error(str(e))


# ---- Smart Contract Interaction ----
st.subheader("📜 Smart Contract Simulation")

contract_types = ['Simple Call (e.g. view balance)',
                  'Medium Call (e.g. transfer ownership)',
                  'Complex Call (e.g. mint NFT, DAO vote)']
chain_info = CHAINS[st.session_state.active_chain]
gas_fees = {level: calculate_gas_fee(chain_info, level) for level in chain_info['contract_multipliers']} 
contract_action = st.selectbox('Select interaction type',
                               [f'{contract_type} - ${gas_fees[contract_type.split(" ")[0].lower()]:.2f}' for contract_type in contract_types]
                                )
contract_level = contract_action.split(' ')[0].lower()

# Define gas multipliers based on complexity
gas_fee = calculate_gas_fee(chain_info, contract_level)
##base_gas = chain_info["gas_fee"]
##gas_multiplier = chain_info["contract_multipliers"][contract_level]
##scaled_gas = base_gas * gas_multiplier

if st.button("Simulate Contract Interaction"):
    balance = get_wallet_balance(user_id, active_wallet["address"])["USDC"]
    if balance < gas_fee: ##scaled_gas:
        st.error(f"Not enough USDC to cover gas (${gas_fee:.2f})")
    else:
        update_wallet_balance(user_id, active_wallet["address"], -gas_fee)

        save_transaction(user_id, {
            "type": "contract_call",
            "wallet": active_wallet["address"],
            "chain": st.session_state.active_chain,
            "timestamp": datetime.utcnow().isoformat(),
            "gas_fee": gas_fee,
            "direction": "out",
            "action": contract_action
        })

        st.success(f"Simulated: {contract_action} (gas: ${gas_fee:.2f})")
        st.rerun()


# ---- Mint NFT ----
st.subheader("🖼 Mint NFT from Portfolio")

catalog = load_catalog()
if not catalog:
    st.info("No portfolio catalog found. Add data/portfolio_catalog.json to enable NFT minting.")
else:
    # Build selection labels
    asset_labels = [f"{a['title']} ({a['asset_id']})" for a in catalog]
    asset_choice = st.selectbox("Choose an artwork to mint", asset_labels)
    asset = catalog[asset_labels.index(asset_choice)]

    # Optional override name/description
    nft_name = st.text_input("NFT Name", value=asset["title"])
    nft_desc = st.text_area("NFT Description", value=asset.get("description", ""))

    # Use current chain for mint cost (treat mint as 'complex contract')
    # Gas fee scaling re-uses your YAML/multipliers
    chain_info = CHAINS[st.session_state.active_chain]
    gas_fee = calculate_gas_fee(chain_info, 'complex')
    st.info(f"Mint cost (gas): ${gas_fee:.2f} on {st.session_state.active_chain}")

    if st.button("Mint NFT"):
        # Check funds
        bal = get_wallet_balance(user_id, active_wallet["address"])["USDC"]
        if bal < gas_fee:
            st.error("Insufficient USDC to cover mint gas.")
        else:
            # Deduct gas
            update_wallet_balance(user_id, active_wallet["address"], -gas_fee)

            # Mint NFT
            nft = mint_nft(
                asset={**asset, "title": nft_name, "description": nft_desc},
                chain=st.session_state.active_chain,
                owner_user=user_id,
                owner_address=active_wallet["address"]
            )

            # Log tx
            save_transaction(user_id, {
                "type": "nft_mint",
                "wallet": active_wallet["address"],
                "token_id": nft["token_id"],
                "asset_id": nft["asset_id"],
                "amount": 0,
                "chain": st.session_state.active_chain,
                "timestamp": datetime.utcnow().isoformat(),
                "gas_fee": gas_fee,
                "direction": "out"
            })

            st.success(f"Minted NFT '{nft_name}' (Token {nft['token_id'][:8]}…)!")
            st.rerun()


# ---- Transaction History ----
st.subheader("📜 Transaction History")

txs = load_transactions(user_id)
wallet_addr = active_wallet["address"]
wallet_txs = [tx for tx in txs if tx["wallet"] == wallet_addr]

if wallet_txs:
    for tx in reversed(wallet_txs[-25:]):  # show latest 25
        ts = tx.get("timestamp", "unknown").replace("T", " ").split(".")[0]
        kind = tx["type"]
        amt = tx.get("amount")
        chain = tx.get("chain", "")
        gas = tx.get("gas_fee", 0)
        direction = tx.get("direction", "in")

        match kind:
            case 'transfer_sent':
                target = tx.get("recipient", "unknown")
                st.write(f"🟥 [{ts}] Sent {amt:.2f} USDC → `{target[:6]}…{target[-4:]}` on {chain} (gas: ${gas})")
            case 'transfer_received':
                sender = tx.get("sender", "unknown")
                st.write(f"🟩 [{ts}] Received {amt:.2f} USDC ← `{sender[:6]}…{sender[-4:]}` on {chain}")
            case 'onramp':
                st.write(f"💸 [{ts}] On-ramped {amt:.2f} USDC on {chain}")
            case 'offramp':
                st.write(f"🏦 [{ts}] Off-ramped {amt:.2f} USDC on {chain}")
            case 'contract_call':
                action = tx.get("action", "Unknown action")
                st.write(f"📜 [{ts}] Contract Interaction – {action} on {chain} (gas: ${gas})")
            case 'nft_mint':
                name = tx.get("asset_id", "NFT")
                st.write(f"🖼 [{ts}] Minted NFT {name} on {chain} (gas: ${gas})")
            case 'nft_transfer':
                token = tx.get("token_id", "")
                to_addr = tx.get("recipient", "")
                st.write(f"🖼🔁 [{ts}] Sent NFT {token[:8]}… to `{to_addr[:6]}…{to_addr[-4:]}` on {chain} (gas: ${gas})")
            case 'nft_received':
                from_addr = tx.get('sender', '')
                token = tx.get('token_id', '')
                st.write(f"🖼⬅️ [{ts}] Received NFT {token[:8]}… from `{from_addr[:6]}…{from_addr[-4:]}` on {chain}")
            case 'nft_burn':
                token = tx.get("token_id", "")
                st.write(f"🔥 [{ts}] Burned NFT {token[:8]}… on {chain} (gas: ${gas})")




else:
    st.info("No transactions yet for this wallet.")


# ---- Chain Selection ----
st.subheader("🌐 Select Network")

chain_names = list(CHAINS.keys())

# Track selected chain in session
if "active_chain" not in st.session_state:
    st.session_state.active_chain = chain_names[0]

selected_chain = st.selectbox("Choose blockchain network", chain_names, index=chain_names.index(st.session_state.active_chain))
st.session_state.active_chain = selected_chain

chain_info = CHAINS[selected_chain]
st.info(f"Gas Fee Estimate: ${chain_info['gas_fee']} per transaction on {selected_chain}")

# ---- Wallet Details ----
with st.expander("🔐 Active Wallet Details"):
    st.markdown(f"**Address:** `{active_wallet['address']}`")
    st.markdown(f"**Private Key:** `{active_wallet['private_key']}`")
    if active_wallet.get("nickname"):
        st.markdown(f"**Nickname:** {active_wallet['nickname']}")

# ---- Edit Nickname ----
st.subheader("✏️ Rename Active Wallet")

new_nickname = st.text_input("Enter a new nickname", value=active_wallet.get("nickname", ""))
if st.button("Update Nickname"):
    from wallet import update_wallet_nickname
    update_wallet_nickname(user_id, active_wallet["address"], new_nickname)
    st.session_state.active_wallet_address = active_wallet["address"]
    st.rerun()
    st.success("Nickname updated!")

# ---- Delete Wallet ----
st.subheader("🗑️ Delete Wallet")

if st.button("Delete Active Wallet"):
    from wallet import delete_wallet
    delete_wallet(user_id, active_wallet["address"])
    st.warning("Wallet deleted. Refreshing...")
    st.rerun()
