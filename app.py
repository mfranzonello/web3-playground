import streamlit as st
from wallet import create_wallet, get_wallets

st.set_page_config(page_title="SimChain", layout="wide")

st.title("🔗 SimChain – Web3 Simulation Dashboard")

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
