import streamlit as st
from wallet import create_wallet, get_wallets, load_all_wallets
from balances import get_wallet_balance, update_wallet_balance, transfer, off_ramp
from chains import CHAINS
from transactions import save_transaction, load_transactions
from datetime import datetime


st.set_page_config(page_title="SimChain", layout="wide")

# Initialize session state for active wallet
if "active_wallet_address" not in st.session_state:
    st.session_state.active_wallet_address = None

# ---- User Login ----
st.sidebar.header("👤 User Login")
user_id = st.sidebar.text_input("Enter your username", value="")

if not user_id:
    st.title("🔗 SimChain – Web3 Simulation Dashboard")
    st.warning("Please enter a username in the sidebar to get started.")
    st.stop()

WALLET_FILE = f"data/{user_id}_wallets.json"


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

# ---- Transfer Funds ----
# ---- Transfer Funds ----
st.subheader("🔁 Simulate USDC Transfer")

all_wallets = load_all_wallets()
recipient_options = [
    f"{w['nickname']} ({w['address'][:6]}…{w['address'][-4:]}) — @{w['user_id']}"
    if w['nickname'] else f"{w['address']} — @{w['user_id']}"
    for w in all_wallets if w['address'] != active_wallet["address"]
]
recipient_wallets = [w for w in all_wallets if w['address'] != active_wallet["address"]]

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

# ---- Transaction History ----
st.subheader("📜 Transaction History")

txs = load_transactions(user_id)
wallet_addr = active_wallet["address"]
wallet_txs = [tx for tx in txs if tx["wallet"] == wallet_addr]

if wallet_txs:
    for tx in reversed(wallet_txs[-25:]):  # show latest 25
        ts = tx.get("timestamp", "unknown").replace("T", " ").split(".")[0]
        kind = tx["type"]
        amt = tx["amount"]
        chain = tx.get("chain", "")
        gas = tx.get("gas_fee", 0)
        direction = tx.get("direction", "in")

        if kind == "transfer_sent":
            target = tx.get("recipient", "unknown")
            st.write(f"🟥 [{ts}] Sent {amt:.2f} USDC → `{target[:6]}…{target[-4:]}` on {chain} (gas: ${gas})")
        elif kind == "transfer_received":
            sender = tx.get("sender", "unknown")
            st.write(f"🟩 [{ts}] Received {amt:.2f} USDC ← `{sender[:6]}…{sender[-4:]}` on {chain}")
        elif kind == "onramp":
            st.write(f"💸 [{ts}] On-ramped {amt:.2f} USDC on {chain}")
        elif kind == "offramp":
            st.write(f"🏦 [{ts}] Off-ramped {amt:.2f} USDC on {chain}")
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
