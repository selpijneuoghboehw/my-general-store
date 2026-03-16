"""
Sanjay Karyana Store — Dark Theme Edition  (v3.0 — PIN Lock)
Run: streamlit run app.py
"""

import os
import re
import time
from datetime import datetime

import pandas as pd
import streamlit as st

# ─── Constants ────────────────────────────────────────────────────────────────
INVENTORY_FILE  = "inventory.csv"
ORDERS_FILE     = "orders.csv"
ORDERS_COLS     = ["Time", "Customer", "Items", "Total"]

OWNER_PIN       = "1969"        # ← Change this to your preferred PIN
MAX_ATTEMPTS    = 5             # Wrong attempts before lockout
LOCKOUT_SECONDS = 30            # Lockout duration in seconds

DUMMY_INVENTORY = pd.DataFrame([
    {"item_name": "Rice",          "category": "Pulses",   "price": 60},
    {"item_name": "Chana Dal",     "category": "Pulses",   "price": 105},
    {"item_name": "Moong Dal",     "category": "Pulses",   "price": 120},
    {"item_name": "Masoor Dal",    "category": "Pulses",   "price": 95},
    {"item_name": "Toor Dal",      "category": "Pulses",   "price": 110},
    {"item_name": "Soap",          "category": "Cleaning", "price": 30},
    {"item_name": "Detergent",     "category": "Cleaning", "price": 85},
    {"item_name": "Floor Cleaner", "category": "Cleaning", "price": 120},
    {"item_name": "Sugar",         "category": "Grocery",  "price": 45},
    {"item_name": "Salt",          "category": "Grocery",  "price": 20},
    {"item_name": "Tea Powder",    "category": "Grocery",  "price": 250},
    {"item_name": "Biscuits",      "category": "Snacks",   "price": 40},
    {"item_name": "Chips",         "category": "Snacks",   "price": 20},
])

CAT_ICONS = {
    "Pulses":   "🌾",
    "Cleaning": "🧹",
    "Grocery":  "🛒",
    "Snacks":   "🍿",
}

# ─── File helpers ──────────────────────────────────────────────────────────────

def load_inventory() -> pd.DataFrame:
    if not os.path.exists(INVENTORY_FILE):
        DUMMY_INVENTORY.to_csv(INVENTORY_FILE, index=False)
    df = pd.read_csv(INVENTORY_FILE)
    for col in ["item_name", "category", "price"]:
        if col not in df.columns:
            df[col] = ""
    df["item_name"] = df["item_name"].fillna("").astype(str).str.strip()
    df["category"]  = df["category"].fillna("Uncategorised").astype(str).str.strip()
    df["price"]     = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df = df[df["item_name"] != ""].reset_index(drop=True)
    return df


def load_orders() -> pd.DataFrame:
    if not os.path.exists(ORDERS_FILE):
        empty = pd.DataFrame(columns=ORDERS_COLS)
        empty.to_csv(ORDERS_FILE, index=False)
        return empty
    try:
        df = pd.read_csv(ORDERS_FILE, on_bad_lines="skip")
    except Exception:
        df = pd.DataFrame(columns=ORDERS_COLS)
    for col in ORDERS_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[ORDERS_COLS]


def save_order(customer: str, cart: list, total: float):
    items_str = ", ".join(
        f"{row['display']} {row['item']} (@ ₹{row['price']})"
        for row in cart
    )
    new_row = pd.DataFrame([{
        "Time":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Customer": customer.strip() or "Guest",
        "Items":    items_str,
        "Total":    total,
    }])
    existing = load_orders()
    updated  = pd.concat([existing, new_row], ignore_index=True)
    updated.to_csv(ORDERS_FILE, index=False)


def clear_orders():
    pd.DataFrame(columns=ORDERS_COLS).to_csv(ORDERS_FILE, index=False)

# ─── Session-state bootstrap ──────────────────────────────────────────────────

def init_state():
    defaults = {
        "cart":               [],
        "selected_category":  None,
        "owner_authenticated": False,
        "pin_buffer":         "",
        "pin_attempts":       0,
        "pin_locked_until":   0.0,
        "pin_shake":          False,
        "pin_message":        "",
        "editing_order_idx":  None,
        "edit_items":         [],
        "cust_search":        "",
        "owner_search":       "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# ─── CSS ──────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Roboto:wght@300;400;500;700&display=swap');

    :root {
        --bg-base:       #0D0F14;
        --bg-surface:    #141720;
        --bg-card:       #1C202E;
        --bg-elevated:   #242838;
        --accent:        #F5A623;
        --accent-dim:    #C4811A;
        --accent-glow:   rgba(245,166,35,0.18);
        --accent-glow2:  rgba(245,166,35,0.08);
        --green:         #22C55E;
        --green-glow:    rgba(34,197,94,0.18);
        --red:           #EF4444;
        --red-glow:      rgba(239,68,68,0.18);
        --text-primary:  #F0F2FF;
        --text-secondary:#9AA0B8;
        --text-muted:    #5A6080;
        --border:        rgba(255,255,255,0.07);
        --border-accent: rgba(245,166,35,0.35);
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Roboto', sans-serif !important;
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
    }

    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"]  { display: none !important; }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1100px !important;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 10px; }

    /* ── Store Header ─────────────────── */
    .store-header {
        position: relative; background: var(--bg-card);
        border: 1px solid var(--border-accent); border-radius: 20px;
        padding: 1.6rem 2rem; margin-bottom: 1.8rem; overflow: hidden;
    }
    .store-header::before {
        content: ''; position: absolute; top: -60px; right: -60px;
        width: 200px; height: 200px;
        background: radial-gradient(circle, var(--accent-glow), transparent 70%);
        pointer-events: none;
    }
    .store-header h1 {
        font-family: 'Inter', sans-serif !important; font-weight: 800;
        font-size: 2rem; color: var(--accent) !important;
        margin: 0 0 4px 0; letter-spacing: -0.5px;
        text-shadow: 0 0 30px var(--accent-glow);
    }
    .store-header p {
        color: var(--text-secondary) !important; font-size: 0.88rem;
        margin: 0; letter-spacing: 0.8px; text-transform: uppercase;
    }
    .store-header .badge {
        display: inline-block; background: var(--accent-glow);
        border: 1px solid var(--border-accent); color: var(--accent);
        font-size: 0.72rem; font-weight: 600; padding: 2px 10px;
        border-radius: 20px; letter-spacing: 0.5px; margin-top: 8px;
    }

    /* ── Section Labels ───────────────── */
    .section-label {
        font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.05rem;
        color: var(--text-primary); margin: 1.4rem 0 0.8rem 0;
        display: flex; align-items: center; gap: 8px;
    }
    .section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

    /* ── Name Banner ──────────────────── */
    .name-banner {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: 16px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
    }
    .name-banner p {
        font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.1rem;
        color: var(--text-primary); margin: 0 0 0.8rem 0;
    }

    /* ── Inputs ───────────────────────── */
    .stTextInput input {
        background: var(--bg-elevated) !important; border: 1px solid var(--border) !important;
        border-radius: 10px !important; color: var(--text-primary) !important;
        font-family: 'Roboto', sans-serif !important; padding: 0.6rem 1rem !important;
        transition: border-color .2s !important;
    }
    .stTextInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-glow2) !important; }
    .stTextInput label { color: var(--text-secondary) !important; font-size: 0.85rem !important; }
    .stNumberInput input {
        background: var(--bg-elevated) !important; border: 1px solid var(--border) !important;
        border-radius: 10px !important; color: var(--text-primary) !important;
        font-family: 'Roboto', sans-serif !important;
    }
    .stNumberInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-glow2) !important; }
    .stNumberInput button { background: var(--bg-elevated) !important; border-color: var(--border) !important; color: var(--accent) !important; }

    /* ── Radio ────────────────────────── */
    .stRadio label { color: var(--text-secondary) !important; font-size: 0.9rem !important; }
    .stRadio [data-testid="stMarkdownContainer"] p { color: var(--text-secondary) !important; }

    /* ── Category cards ───────────────── */
    .cat-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: 18px; padding: 1.4rem 1rem; text-align: center;
        transition: all .22s ease; margin-bottom: 6px;
    }
    .cat-card .cat-icon { font-size: 2.2rem; line-height: 1; margin-bottom: 0.5rem; }
    .cat-card .cat-name { font-family: 'Inter', sans-serif; font-weight: 700; font-size: 0.95rem; color: var(--text-primary); }
    .cat-card .cat-count { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

    /* ── Item cards ───────────────────── */
    .item-card {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: 16px; padding: 1rem 1.3rem 0.4rem 1.3rem; margin-bottom: 4px;
    }
    .item-card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 0.5rem; }
    .item-name { font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1rem; color: var(--text-primary); }
    .item-price-tag {
        background: var(--accent-glow); border: 1px solid var(--border-accent);
        color: var(--accent); font-size: 0.78rem; font-weight: 600; padding: 2px 10px; border-radius: 20px;
    }

    /* ── Buttons base ─────────────────── */
    .stButton > button {
        font-family: 'Roboto', sans-serif !important;
        border-radius: 10px !important; transition: all .2s !important; font-weight: 500 !important;
    }

    /* ══ ADD BUTTON — solid orange, always visible on any background ══ */
    .add-btn .stButton > button {
        background: #F5A623 !important;
        border: none !important;
        color: #0D0F14 !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        width: 100% !important;
        padding: 0.5rem 0.8rem !important;
        border-radius: 10px !important;
        box-shadow: 0 3px 12px rgba(245,166,35,0.45) !important;
        letter-spacing: 0.2px !important;
    }
    .add-btn .stButton > button:hover {
        background: #E09410 !important;
        color: #0D0F14 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(245,166,35,0.6) !important;
    }
    .add-btn .stButton > button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(245,166,35,0.4) !important;
    }

    .back-btn .stButton > button {
        background: transparent !important; border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important; font-size: 0.85rem !important; padding: 0.35rem 0.8rem !important;
    }
    .back-btn .stButton > button:hover { border-color: var(--accent) !important; color: var(--accent) !important; }

    .confirm-btn .stButton > button {
        background: linear-gradient(135deg, var(--green), #16A34A) !important;
        border: none !important; color: white !important;
        font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
        font-size: 1rem !important; letter-spacing: 0.3px !important;
        border-radius: 12px !important; width: 100% !important; padding: 0.65rem 1rem !important;
        box-shadow: 0 4px 18px var(--green-glow) !important;
    }
    .confirm-btn .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(34,197,94,0.35) !important; }

    .clear-btn .stButton > button {
        background: transparent !important; border: 1px solid rgba(239,68,68,0.4) !important;
        color: var(--red) !important; font-size: 0.88rem !important;
        width: 100% !important; padding: 0.65rem 1rem !important;
    }
    .clear-btn .stButton > button:hover { background: rgba(239,68,68,0.1) !important; border-color: var(--red) !important; }

    /* ── Cart ─────────────────────────── */
    .cart-box { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 1.2rem 1.4rem; margin: 0.6rem 0; }
    .total-row {
        background: var(--bg-elevated); border: 1px solid var(--border-accent);
        border-radius: 12px; padding: 0.9rem 1.4rem;
        display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;
    }
    .total-label { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 1rem; color: var(--text-secondary); }
    .total-amount { font-family: 'Inter', sans-serif; font-weight: 800; font-size: 1.5rem; color: var(--accent); text-shadow: 0 0 20px var(--accent-glow); }

    /* ── Dataframe ────────────────────── */
    .stDataFrame { border-radius: 12px !important; overflow: hidden !important; border: 1px solid var(--border) !important; }
    [data-testid="stDataFrame"] > div { background: var(--bg-card) !important; border-radius: 12px !important; }

    /* ── Alerts ───────────────────────── */
    .stAlert { border-radius: 12px !important; border: 1px solid var(--border) !important; background: var(--bg-card) !important; }

    /* ── Expander ─────────────────────── */
    .stExpander { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 14px !important; margin-bottom: 10px !important; }
    .stExpander:hover { border-color: var(--border-accent) !important; }
    .stExpander summary { font-family: 'Inter', sans-serif !important; font-weight: 600 !important; color: var(--text-primary) !important; padding: 0.85rem 1.2rem !important; }
    .stExpander [data-testid="stExpanderDetails"] { background: var(--bg-elevated) !important; border-top: 1px solid var(--border) !important; padding: 1rem 1.2rem !important; }

    hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1rem 0 !important; }

    /* ── Owner stats ──────────────────── */
    .stat-strip { display: flex; gap: 14px; margin-bottom: 1.4rem; flex-wrap: wrap; }
    .stat-card { flex: 1; min-width: 120px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.2rem; }
    .stat-card .stat-val { font-family: 'Inter', sans-serif; font-weight: 800; font-size: 1.6rem; color: var(--accent); }
    .stat-card .stat-lbl { font-size: 0.78rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.6px; margin-top: 2px; }

    .stCaption, small { color: var(--text-muted) !important; }
    [data-testid="stToast"] { background: var(--bg-elevated) !important; border: 1px solid var(--border-accent) !important; border-radius: 12px !important; color: var(--text-primary) !important; }

    /* ── Search Bar ──────────────────── */
    .search-wrap { position: relative; margin-bottom: 1.1rem; }
    .search-wrap input {
        background: var(--bg-card) !important; border: 1.5px solid var(--border) !important;
        border-radius: 14px !important; color: var(--text-primary) !important;
        font-size: 1rem !important; padding: 0.7rem 1rem !important;
        transition: border-color .2s, box-shadow .2s !important; width: 100% !important;
    }
    .search-wrap input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-glow2) !important; }
    .search-wrap input::placeholder { color: var(--text-muted) !important; }

    /* ── Order Edit Panel ────────────── */
    .edit-panel { background: var(--bg-base); border: 1px solid var(--border-accent); border-radius: 14px; padding: 1.1rem 1.3rem; margin-top: 0.8rem; }
    .edit-panel-title { font-family: "Inter", sans-serif; font-weight: 700; font-size: 0.95rem; color: var(--accent); margin-bottom: 0.8rem; }
    .edit-total-row {
        background: var(--bg-elevated); border: 1px solid var(--border-accent);
        border-radius: 10px; padding: 0.6rem 1rem;
        display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem;
    }
    .remove-item-btn .stButton > button {
        background: transparent !important; border: 1px solid rgba(239,68,68,0.35) !important;
        color: var(--red) !important; font-size: 0.78rem !important;
        padding: 0.2rem 0.5rem !important; border-radius: 7px !important; min-width: 32px !important;
    }
    .remove-item-btn .stButton > button:hover { background: rgba(239,68,68,0.12) !important; border-color: var(--red) !important; }

    /* ── Inventory Manager ────────────── */
    .inv-item-label { font-size: 0.95rem; font-weight: 500; color: var(--text-primary); padding: 0.45rem 0; border-bottom: 1px solid var(--border); }
    .inv-save-btn .stButton > button {
        background: linear-gradient(135deg, var(--accent), var(--accent-dim)) !important;
        border: none !important; color: var(--bg-base) !important; font-weight: 700 !important;
        font-size: 0.95rem !important; border-radius: 12px !important; padding: 0.6rem 1rem !important;
        box-shadow: 0 4px 16px var(--accent-glow) !important;
    }
    .inv-save-btn .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 22px rgba(245,166,35,0.4) !important; }
    .inv-add-btn .stButton > button {
        background: var(--bg-elevated) !important; border: 1px solid var(--border-accent) !important;
        color: var(--accent) !important; font-weight: 600 !important; font-size: 0.95rem !important;
        border-radius: 12px !important; padding: 0.6rem 1rem !important;
    }
    .inv-add-btn .stButton > button:hover { background: var(--accent) !important; color: var(--bg-base) !important; box-shadow: 0 4px 14px rgba(245,166,35,0.3) !important; }
    .stSelectbox > div > div { background: var(--bg-elevated) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; color: var(--text-primary) !important; }
    .stSelectbox label { color: var(--text-secondary) !important; font-size: 0.85rem !important; }

    /* ── Tab navigation ───────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important; border: 1px solid var(--border) !important;
        border-radius: 14px !important; padding: 5px 6px !important; gap: 4px !important; margin-bottom: 1.4rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; border: none !important; border-radius: 10px !important;
        color: var(--text-muted) !important; font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important; font-size: 0.95rem !important; padding: 0.55rem 1.4rem !important;
        transition: all .18s ease !important; white-space: nowrap !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text-primary) !important; background: var(--bg-elevated) !important; }
    .stTabs [aria-selected="true"] { background: var(--accent) !important; color: var(--bg-base) !important; font-weight: 700 !important; box-shadow: 0 2px 12px var(--accent-glow) !important; }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-border"]    { display: none !important; }

    /* ════ PIN LOCK STYLES ════ */
    .pin-wrapper { display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem 2.5rem; }
    .pin-lock-icon { width: 72px; height: 72px; background: var(--accent-glow); border: 2px solid var(--border-accent); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin-bottom: 1.2rem; box-shadow: 0 0 32px var(--accent-glow); }
    .pin-title { font-family: 'Inter', sans-serif; font-weight: 800; font-size: 1.45rem; color: var(--text-primary); margin: 0 0 4px 0; text-align: center; }
    .pin-subtitle { font-size: 0.85rem; color: var(--text-muted); text-align: center; margin-bottom: 1.8rem; }
    .pin-dots { display: flex; gap: 14px; margin-bottom: 0.6rem; justify-content: center; }
    .pin-dot { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--text-muted); background: transparent; transition: all .18s ease; }
    .pin-dot.filled { background: var(--accent); border-color: var(--accent); box-shadow: 0 0 10px var(--accent-glow); }
    .pin-dot.error  { border-color: var(--red); background: var(--red); box-shadow: 0 0 10px var(--red-glow); }
    .pin-msg-ok    { font-size: 0.82rem; color: var(--green);  text-align: center; min-height: 1.2em; margin-bottom: 1.2rem; }
    .pin-msg-err   { font-size: 0.82rem; color: var(--red);    text-align: center; min-height: 1.2em; margin-bottom: 1.2rem; }
    .pin-msg-warn  { font-size: 0.82rem; color: var(--accent); text-align: center; min-height: 1.2em; margin-bottom: 1.2rem; }
    .pin-msg-empty { font-size: 0.82rem; color: transparent;   text-align: center; min-height: 1.2em; margin-bottom: 1.2rem; }
    .pin-submit-btn .stButton > button { background: linear-gradient(135deg, var(--accent), var(--accent-dim)) !important; border: none !important; color: var(--bg-base) !important; font-family: 'Inter', sans-serif !important; font-weight: 800 !important; font-size: 1rem !important; border-radius: 14px !important; padding: 0.65rem 2rem !important; width: 100% !important; box-shadow: 0 4px 18px var(--accent-glow) !important; }
    .pin-submit-btn .stButton > button:hover { transform: translateY(-2px) !important; }
    .lock-btn .stButton > button { background: transparent !important; border: 1px solid var(--border-accent) !important; color: var(--accent) !important; font-size: 0.82rem !important; padding: 0.3rem 0.9rem !important; border-radius: 8px !important; }
    .lock-btn .stButton > button:hover { background: var(--accent-glow) !important; }
    .lockout-card { background: rgba(239,68,68,0.07); border: 1px solid rgba(239,68,68,0.3); border-radius: 14px; padding: 1.2rem 1.6rem; text-align: center; margin: 1rem 0; }
    .lockout-card .lc-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .lockout-card .lc-title { font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1rem; color: var(--red); margin-bottom: 4px; }
    .lockout-card .lc-msg { font-size: 0.82rem; color: var(--text-muted); }
    </style>
    """, unsafe_allow_html=True)

# ─── PIN lock screen ──────────────────────────────────────────────────────────

def pin_lock_screen() -> bool:
    if st.session_state.owner_authenticated:
        return True

    now = time.time()
    locked_until = st.session_state.pin_locked_until
    is_locked    = now < locked_until

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div class="pin-wrapper">
            <div class="pin-lock-icon">🔐</div>
            <div class="pin-title">Owner Dashboard</div>
            <div class="pin-subtitle">Enter your 4-digit PIN to continue</div>
        </div>
        """, unsafe_allow_html=True)

        if is_locked:
            secs_left = int(locked_until - now) + 1
            st.markdown(f"""
            <div class="lockout-card">
                <div class="lc-icon">🚫</div>
                <div class="lc-title">Too many wrong attempts</div>
                <div class="lc-msg">Please wait <strong style="color:#EF4444">{secs_left}s</strong> before trying again.</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1)
            st.rerun()
            return False

        buf       = st.session_state.pin_buffer
        pin_len   = len(OWNER_PIN)
        dot_class = "error" if st.session_state.pin_shake else "filled"

        dots_html = '<div class="pin-dots">'
        for i in range(pin_len):
            dots_html += f'<div class="pin-dot {dot_class}"></div>' if i < len(buf) else '<div class="pin-dot"></div>'
        dots_html += "</div>"
        st.markdown(dots_html, unsafe_allow_html=True)

        msg = st.session_state.pin_message
        msg_cls = "pin-msg-empty"
        if msg.startswith("✅"):   msg_cls = "pin-msg-ok"
        elif msg.startswith("❌"): msg_cls = "pin-msg-err"
        elif msg.startswith("⚠"): msg_cls = "pin-msg-warn"
        st.markdown(f'<div class="{msg_cls}">{msg if msg else "&nbsp;"}</div>', unsafe_allow_html=True)

        digit_rows = [["1","2","3"],["4","5","6"],["7","8","9"],["__empty__","0","__del__"]]
        for row in digit_rows:
            cols = st.columns(3)
            for col, key in zip(cols, row):
                with col:
                    if key == "__empty__":
                        st.markdown("", unsafe_allow_html=True)
                    elif key == "__del__":
                        st.markdown('<div style="display:flex;justify-content:center;">', unsafe_allow_html=True)
                        if st.button("⌫", key="pin_del", use_container_width=True):
                            st.session_state.pin_buffer  = buf[:-1]
                            st.session_state.pin_shake   = False
                            st.session_state.pin_message = ""
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        if st.button(key, key=f"pin_{key}", use_container_width=True):
                            if len(buf) < pin_len:
                                new_buf = buf + key
                                st.session_state.pin_buffer  = new_buf
                                st.session_state.pin_shake   = False
                                st.session_state.pin_message = ""
                                if len(new_buf) == pin_len:
                                    if new_buf == OWNER_PIN:
                                        st.session_state.owner_authenticated = True
                                        st.session_state.pin_buffer   = ""
                                        st.session_state.pin_attempts = 0
                                        st.session_state.pin_message  = "✅ Access granted"
                                        st.session_state.pin_shake    = False
                                        st.rerun()
                                    else:
                                        st.session_state.pin_attempts += 1
                                        remaining = MAX_ATTEMPTS - st.session_state.pin_attempts
                                        st.session_state.pin_shake = True
                                        if remaining <= 0:
                                            st.session_state.pin_locked_until = time.time() + LOCKOUT_SECONDS
                                            st.session_state.pin_attempts     = 0
                                            st.session_state.pin_message      = f"⚠ Locked for {LOCKOUT_SECONDS}s"
                                        else:
                                            st.session_state.pin_message = f"❌ Wrong PIN — {remaining} attempt{'s' if remaining != 1 else ''} left"
                                        st.session_state.pin_buffer = ""
                                st.rerun()

        if st.session_state.pin_attempts > 0:
            st.markdown(f"<div style='text-align:center;font-size:0.75rem;color:var(--text-muted);margin-top:0.4rem;'>⚠ {st.session_state.pin_attempts}/{MAX_ATTEMPTS} failed attempts</div>", unsafe_allow_html=True)
    return False

# ─── Shared item renderer ──────────────────────────────────────────────────────

def render_item_row(row, inventory, key_prefix: str, is_cart: bool = True):
    item_name  = str(row["item_name"])
    item_price = float(row["price"])
    is_pulse   = str(row["category"]) == "Pulses"
    unit_label = "per kg" if is_pulse else "per unit"

    st.markdown(f"""
    <div class="item-card">
        <div class="item-card-header">
            <span class="item-name">{item_name}</span>
            <span class="item-price-tag">₹{item_price:.0f} {unit_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if is_pulse:
        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        with c1:
            unit = st.radio("Unit", ["kg", "g"], key=f"{key_prefix}_unit_{item_name}", horizontal=True, label_visibility="collapsed")
        with c2:
            if unit == "kg":
                qty_val     = st.number_input("Qty", min_value=0.1, max_value=20.0, step=0.1, value=0.5, key=f"{key_prefix}_qty_{item_name}_kg", label_visibility="collapsed")
                qty_kg      = qty_val
                display_str = f"{qty_val}kg"
            else:
                qty_val     = st.number_input("Qty", min_value=50, max_value=950, step=50, value=500, key=f"{key_prefix}_qty_{item_name}_g", label_visibility="collapsed")
                qty_kg      = qty_val / 1000
                display_str = f"{qty_val}g"
        with c3:
            amount = round(qty_kg * item_price, 2)
            st.markdown(f"<div style='padding:0.5rem 0;color:#9AA0B8;font-size:0.88rem;'>= <span style='color:#F5A623;font-weight:700;font-size:1rem;'>₹{amount}</span></div>", unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            if st.button("＋ Add", key=f"{key_prefix}_add_{item_name}", use_container_width=True):
                if is_cart:
                    st.session_state.cart.append({"item": item_name, "price": item_price, "qty_kg": qty_kg, "display": display_str, "amount": amount})
                    st.toast(f"✅ {display_str} of {item_name} added!")
                else:
                    st.session_state.edit_items.append({"product": item_name, "quantity": display_str, "rate": item_price, "subtotal": amount})
                    st.toast(f"✅ {display_str} of {item_name} added to order!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            qty_units   = st.number_input("Units", min_value=1, max_value=50, step=1, value=1, key=f"{key_prefix}_qty_{item_name}_units", label_visibility="collapsed")
            display_str = f"{qty_units} units"
        with c2:
            amount = round(qty_units * item_price, 2)
            st.markdown(f"<div style='padding:0.5rem 0;color:#9AA0B8;font-size:0.88rem;'>= <span style='color:#F5A623;font-weight:700;font-size:1rem;'>₹{amount}</span></div>", unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="add-btn">', unsafe_allow_html=True)
            if st.button("＋ Add", key=f"{key_prefix}_add_{item_name}", use_container_width=True):
                if is_cart:
                    st.session_state.cart.append({"item": item_name, "price": item_price, "qty_kg": qty_units, "display": display_str, "amount": amount})
                    st.toast(f"✅ {qty_units} × {item_name} added!")
                else:
                    st.session_state.edit_items.append({"product": item_name, "quantity": display_str, "rate": item_price, "subtotal": amount})
                    st.toast(f"✅ {qty_units} × {item_name} added to order!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ─── Customer view ─────────────────────────────────────────────────────────────

def customer_view(inventory: pd.DataFrame):

    st.markdown('<div class="name-banner"><p>👤 Who is shopping today?</p></div>', unsafe_allow_html=True)

    customer_name = st.text_input(
        "Your Name", placeholder="Enter your name to start shopping…",
        key="customer_name_input", label_visibility="collapsed",
    )

    if not customer_name.strip():
        st.markdown("<small>Please enter your name above to browse the store.</small>", unsafe_allow_html=True)
        return

    st.markdown(
        f"<div style='font-family:Inter,sans-serif;font-size:0.9rem;color:#9AA0B8;margin-bottom:0.4rem;'>"
        f"Welcome, <span style='color:#F5A623;font-weight:700'>{customer_name.strip()}</span> ✨</div>",
        unsafe_allow_html=True,
    )

    categories = sorted(inventory["category"].dropna().astype(str).unique().tolist())

    # ── Search bar ─────────────────────────────────────────────────────────────
    st.markdown('<div class="search-wrap">', unsafe_allow_html=True)
    search_query = st.text_input(
        "Search", placeholder="🔍  Search items e.g. Rice, Soap, Dal…",
        key="cust_search_input", label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if search_query.strip():
        q       = search_query.strip().lower()
        matched = inventory[inventory["item_name"].str.lower().str.contains(q, na=False)]
        st.markdown(f'<div class="section-label">🔍 Results for "{search_query.strip()}"</div>', unsafe_allow_html=True)
        if matched.empty:
            st.markdown(f"<small>No items match <b>'{search_query.strip()}'</b>. Try a different word.</small>", unsafe_allow_html=True)
        else:
            for _, row in matched.reset_index(drop=True).iterrows():
                render_item_row(row, inventory, key_prefix="cust_srch", is_cart=True)
    else:
        if st.session_state.selected_category is None:
            st.markdown('<div class="section-label">Browse Categories</div>', unsafe_allow_html=True)
            if not categories:
                st.info("No inventory items found. Ask the owner to add items.")
                return
            cols = st.columns(min(4, len(categories)))
            for idx, cat in enumerate(categories):
                icon     = CAT_ICONS.get(cat, "📦")
                item_cnt = len(inventory[inventory["category"] == cat])
                with cols[idx % len(cols)]:
                    st.markdown(f"""
                    <div class="cat-card">
                        <div class="cat-icon">{icon}</div>
                        <div class="cat-name">{cat}</div>
                        <div class="cat-count">{item_cnt} items</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Shop →", key=f"cat_{cat}", use_container_width=True):
                        st.session_state.selected_category = cat
                        st.rerun()
        else:
            cat  = st.session_state.selected_category
            icon = CAT_ICONS.get(cat, "📦")
            top_l, top_r = st.columns([1, 7])
            with top_l:
                st.markdown('<div class="back-btn">', unsafe_allow_html=True)
                if st.button("← Back", key="back_btn"):
                    st.session_state.selected_category = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with top_r:
                st.markdown(f'<div class="section-label">{icon} {cat}</div>', unsafe_allow_html=True)
            cat_items = inventory[inventory["category"] == cat].reset_index(drop=True)
            for _, row in cat_items.iterrows():
                render_item_row(row, inventory, key_prefix="cust_browse", is_cart=True)

    # ── Cart ───────────────────────────────────────────────────────────────────
    st.markdown("---")
    cart_count = len(st.session_state.cart)
    st.markdown(f'<div class="section-label">🧺 Cart{"" if cart_count == 0 else f" ({cart_count} items)"}</div>', unsafe_allow_html=True)

    if not st.session_state.cart:
        st.markdown("<small>Your cart is empty — add items from a category above.</small>", unsafe_allow_html=True)
        return

    st.markdown('<div class="cart-box">', unsafe_allow_html=True)
    cart_df = pd.DataFrame([{"Item": c["item"], "Weight / Qty": c["display"], "Amount (₹)": c["amount"]} for c in st.session_state.cart])
    st.dataframe(cart_df, use_container_width=True, hide_index=True)
    total = round(sum(c["amount"] for c in st.session_state.cart), 2)
    st.markdown(f'<div class="total-row"><span class="total-label">Grand Total</span><span class="total-amount">₹{total}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    col_clear, col_confirm = st.columns([1, 2])
    with col_clear:
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Clear Cart", key="clear_cart", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_confirm:
        st.markdown('<div class="confirm-btn">', unsafe_allow_html=True)
        if st.button("✅  CONFIRM ORDER", key="confirm_order", use_container_width=True):
            save_order(customer_name, st.session_state.cart, total)
            st.session_state.cart = []
            st.session_state.selected_category = None
            st.balloons()
            st.success("🎉 Order placed! Thank you for shopping at Sanjay Karyana Store.")
        st.markdown("</div>", unsafe_allow_html=True)

# ─── Parse helper ──────────────────────────────────────────────────────────────

def parse_item_row(item_str: str) -> dict:
    rate_match = re.search(r"@\s*₹([\d.]+)", item_str)
    rate       = float(rate_match.group(1)) if rate_match else 0.0
    core       = re.sub(r"\(@\s*₹[\d.]+\)", "", item_str).strip()
    qty_match  = re.match(r"^([\d.]+)\s*(kg|g|units)?\s+(.*)", core)
    if qty_match:
        num_str  = qty_match.group(1).strip()
        unit_str = (qty_match.group(2) or "").strip()
        product  = qty_match.group(3).strip()
    else:
        num_str, unit_str, product = "1", "", core

    num_only = float(num_str) if num_str else 1.0
    qty_num  = num_only / 1000 if unit_str == "g" else num_only

    if unit_str == "units":   display_qty = f"{num_str} units"
    elif unit_str in ("kg","g"): display_qty = f"{num_str}{unit_str}"
    else:                     display_qty = num_str

    return {"product": product, "quantity": display_qty, "rate": rate, "subtotal": round(qty_num * rate, 2)}

# ─── Inventory Manager ─────────────────────────────────────────────────────────

def inventory_manager():
    inv = load_inventory()

    st.markdown('<div class="section-label">✏️ Update Prices</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:var(--text-muted)'>Edit any price below then click <b style='color:var(--accent)'>Save All Changes</b>.</small>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    categories   = sorted(inv["category"].dropna().astype(str).unique().tolist())
    updated_rows = []
    for cat in categories:
        icon = CAT_ICONS.get(cat, "📦")
        st.markdown(f"<div style='font-family:Inter,sans-serif;font-weight:700;font-size:0.82rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin:1rem 0 0.4rem 0'>{icon} {cat}</div>", unsafe_allow_html=True)
        for _, row in inv[inv["category"] == cat].reset_index(drop=True).iterrows():
            item_name  = str(row["item_name"])
            item_price = float(row["price"])
            c_name, c_price = st.columns([3, 1])
            with c_name:
                st.markdown(f"<div class='inv-item-label'>{item_name}</div>", unsafe_allow_html=True)
            with c_price:
                new_price = st.number_input("Price", min_value=0.0, value=item_price, step=0.5, key=f"inv_price_{item_name}", label_visibility="collapsed")
            updated_rows.append({"item_name": item_name, "category": cat, "price": new_price})

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="inv-save-btn">', unsafe_allow_html=True)
    if st.button("💾  Save All Price Changes", key="save_prices", use_container_width=True):
        pd.DataFrame(updated_rows).to_csv(INVENTORY_FILE, index=False)
        st.success("✅ Prices updated successfully!")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-label">➕ Add New Item</div>', unsafe_allow_html=True)
    existing_categories = sorted(inv["category"].dropna().astype(str).unique().tolist())
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Item Name", placeholder="e.g. Urad Dal", key="new_item_name")
    with col2:
        new_price_val = st.number_input("Price (₹ per kg or unit)", min_value=0.0, value=50.0, step=0.5, key="new_item_price")
    col3, col4 = st.columns(2)
    with col3:
        cat_choice = st.selectbox("Category", options=existing_categories + ["➕ New Category…"], key="new_item_cat_select")
    with col4:
        if cat_choice == "➕ New Category…":
            new_cat_name = st.text_input("New Category Name", placeholder="e.g. Dairy", key="new_cat_name")
        else:
            new_cat_name = ""
            st.markdown(f"<div style='padding:0.45rem 0 0 0;color:var(--text-muted);font-size:0.85rem;'>Category: <span style='color:var(--accent);font-weight:600'>{cat_choice}</span></div>", unsafe_allow_html=True)

    final_category = new_cat_name.strip() if cat_choice == "➕ New Category…" else cat_choice
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="inv-add-btn">', unsafe_allow_html=True)
    if st.button("➕  Add Item to Inventory", key="add_new_item", use_container_width=True):
        if not new_name.strip():
            st.error("Please enter an item name.")
        elif not final_category:
            st.error("Please enter a category name.")
        elif new_name.strip().lower() in inv["item_name"].str.lower().tolist():
            st.warning(f"'{new_name.strip()}' already exists in inventory.")
        else:
            pd.concat([inv, pd.DataFrame([{"item_name": new_name.strip(), "category": final_category, "price": new_price_val}])], ignore_index=True).to_csv(INVENTORY_FILE, index=False)
            st.success(f"✅ '{new_name.strip()}' added to {final_category} at ₹{new_price_val}!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-label">🗑️ Remove Item</div>', unsafe_allow_html=True)
    del_col1, del_col2 = st.columns([3, 1])
    with del_col1:
        item_to_delete = st.selectbox("Select item to remove", options=["— select —"] + inv["item_name"].tolist(), key="del_item_select", label_visibility="collapsed")
    with del_col2:
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Remove", key="delete_item", use_container_width=True):
            if item_to_delete == "— select —":
                st.error("Please select an item first.")
            else:
                inv[inv["item_name"] != item_to_delete].reset_index(drop=True).to_csv(INVENTORY_FILE, index=False)
                st.success(f"✅ '{item_to_delete}' removed from inventory.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">📦 Current Inventory</div>', unsafe_allow_html=True)
    display_inv = inv[["item_name", "category", "price"]].copy()
    display_inv.columns = ["Item", "Category", "Price (₹)"]
    st.dataframe(display_inv, use_container_width=True, hide_index=True)

# ─── Owner Dashboard ───────────────────────────────────────────────────────────

def owner_view():
    if not pin_lock_screen():
        return

    _, lock_col = st.columns([8, 1])
    with lock_col:
        st.markdown('<div class="lock-btn">', unsafe_allow_html=True)
        if st.button("🔒 Lock", key="lock_dashboard"):
            st.session_state.owner_authenticated = False
            st.session_state.pin_buffer          = ""
            st.session_state.pin_message         = ""
            st.session_state.pin_shake           = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    orders = load_orders()
    total_revenue    = 0.0
    unique_customers = 0
    if not orders.empty:
        try:
            total_revenue = orders["Total"].astype(float).sum()
        except Exception:
            pass
        unique_customers = orders["Customer"].nunique()

    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-card"><div class="stat-val">{len(orders)}</div><div class="stat-lbl">Total Orders</div></div>
        <div class="stat-card"><div class="stat-val">₹{total_revenue:,.0f}</div><div class="stat-lbl">Total Revenue</div></div>
        <div class="stat-card"><div class="stat-val">{unique_customers}</div><div class="stat-lbl">Customers</div></div>
    </div>
    """, unsafe_allow_html=True)

    tab_orders, tab_inventory = st.tabs(["📋  Order History", "📦  Manage Inventory"])

    with tab_orders:
        st.markdown('<div class="section-label">📋 Order History</div>', unsafe_allow_html=True)
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        if st.button("🗑️  Clear All Messy Data", key="clear_orders"):
            clear_orders()
            st.session_state.editing_order_idx = None
            st.session_state.edit_items        = []
            st.success("Order data cleared and reset.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if orders.empty:
            st.markdown("<small>No orders recorded yet. Confirmed orders will appear here.</small>", unsafe_allow_html=True)
        else:
            inv        = load_inventory()
            orders_rev = orders.iloc[::-1].reset_index()
            for _, order in orders_rev.iterrows():
                orig_idx  = int(order["index"])
                customer  = str(order.get("Customer", "Guest") or "Guest").strip() or "Guest"
                total_val = order.get("Total", "0")
                items_str = str(order.get("Items", ""))
                time_str  = str(order.get("Time", "—"))
                try:
                    total_disp = f"₹{float(total_val):.2f}"
                except (ValueError, TypeError):
                    total_disp = "₹—"

                with st.expander(f"👤  {customer}   ·   💰 {total_disp}   ·   🕐 {time_str}"):
                    item_parts = [p.strip() for p in items_str.split(",") if p.strip()]
                    rows = []
                    for sno, part in enumerate(item_parts, start=1):
                        p = parse_item_row(part)
                        rows.append({"S.No": sno, "Product": p["product"], "Quantity": p["quantity"], "Rate": f"₹{p['rate']:.2f}", "Subtotal": f"₹{p['subtotal']:.2f}"})
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.caption("(No item details could be parsed)")

                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                    ecol1, _ = st.columns([1, 5])
                    with ecol1:
                        st.markdown('<div class="inv-add-btn">', unsafe_allow_html=True)
                        if st.button("✏️ Edit Order", key=f"edit_btn_{orig_idx}"):
                            st.session_state.editing_order_idx = orig_idx
                            st.session_state.edit_items = [parse_item_row(p.strip()) for p in items_str.split(",") if p.strip()]
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state.editing_order_idx == orig_idx:
                        edit_items = st.session_state.edit_items
                        st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="edit-panel-title">✏️ Editing Order</div>', unsafe_allow_html=True)

                        if edit_items:
                            st.markdown("<div style='font-size:0.8rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px'>Current Items</div>", unsafe_allow_html=True)
                            for i, item in enumerate(edit_items):
                                rc1, rc2, rc3, rc4 = st.columns([3, 2, 2, 1])
                                with rc1:
                                    st.markdown(f"<div style='padding:0.4rem 0;font-size:0.92rem;color:var(--text-primary);font-weight:500'>{item['product']}</div>", unsafe_allow_html=True)
                                with rc2:
                                    st.markdown(f"<div style='padding:0.4rem 0;font-size:0.88rem;color:var(--text-secondary)'>{item['quantity']}</div>", unsafe_allow_html=True)
                                with rc3:
                                    st.markdown(f"<div style='padding:0.4rem 0;font-size:0.88rem;color:var(--accent)'>₹{item['subtotal']:.2f}</div>", unsafe_allow_html=True)
                                with rc4:
                                    st.markdown('<div class="remove-item-btn">', unsafe_allow_html=True)
                                    if st.button("✕", key=f"remove_{orig_idx}_{i}"):
                                        st.session_state.edit_items.pop(i)
                                        st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<small style='color:var(--text-muted)'>No items left — add one below or cancel.</small>", unsafe_allow_html=True)

                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                        st.markdown("<div style='font-size:0.8rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px'>Search & Add Item</div>", unsafe_allow_html=True)
                        st.markdown('<div class="search-wrap">', unsafe_allow_html=True)
                        owner_srch = st.text_input("Search item", placeholder="🔍  Type item name e.g. Rice, Soap…", key=f"owner_srch_{orig_idx}", label_visibility="collapsed")
                        st.markdown("</div>", unsafe_allow_html=True)

                        if owner_srch.strip():
                            q_own       = owner_srch.strip().lower()
                            matched_own = inv[inv["item_name"].str.lower().str.contains(q_own, na=False)]
                            if matched_own.empty:
                                st.markdown(f"<small style='color:var(--text-muted)'>No items match '{owner_srch.strip()}'.</small>", unsafe_allow_html=True)
                            else:
                                for _, mrow in matched_own.reset_index(drop=True).iterrows():
                                    render_item_row(mrow, inv, key_prefix=f"own_edit_{orig_idx}", is_cart=False)
                        else:
                            st.markdown("<small style='color:var(--text-muted)'>Start typing an item name above to find and add it.</small>", unsafe_allow_html=True)

                        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                        new_total = round(sum(x["subtotal"] for x in st.session_state.edit_items), 2)
                        st.markdown(f"<div class='edit-total-row'><span style='color:var(--text-secondary)'>Updated Total</span><span style='color:var(--accent);font-weight:800;font-size:1.1rem'>₹{new_total}</span></div>", unsafe_allow_html=True)
                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

                        sc1, sc2 = st.columns(2)
                        with sc1:
                            st.markdown('<div class="confirm-btn">', unsafe_allow_html=True)
                            if st.button("💾 Save Changes", key=f"save_edit_{orig_idx}", use_container_width=True):
                                if not st.session_state.edit_items:
                                    st.error("Order must have at least one item.")
                                else:
                                    new_items_str = ", ".join(f"{ei['quantity']} {ei['product']} (@ ₹{ei['rate']})" for ei in st.session_state.edit_items)
                                    all_orders = load_orders()
                                    all_orders.at[orig_idx, "Items"] = new_items_str
                                    all_orders.at[orig_idx, "Total"] = new_total
                                    all_orders.to_csv(ORDERS_FILE, index=False)
                                    st.session_state.editing_order_idx = None
                                    st.session_state.edit_items        = []
                                    st.success("✅ Order updated successfully!")
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        with sc2:
                            st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
                            if st.button("✕ Cancel", key=f"cancel_edit_{orig_idx}", use_container_width=True):
                                st.session_state.editing_order_idx = None
                                st.session_state.edit_items        = []
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

    with tab_inventory:
        inventory_manager()

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Sanjay Karyana Store",
        page_icon="🛒",
        layout="wide",
    )
    inject_css()
    init_state()

    inventory = load_inventory()

    st.markdown("""
    <div class="store-header">
        <h1>🏪 Sanjay Karyana Store</h1>
        <p>Fresh &nbsp;·&nbsp; Trusted &nbsp;·&nbsp; Local</p>
        <div class="badge">EST. 2015 &nbsp;·&nbsp; MASHKA</div>
    </div>
    """, unsafe_allow_html=True)

    lock_indicator = " 🔓" if st.session_state.get("owner_authenticated") else " 🔒"
    tab_customer, tab_owner = st.tabs([
        "🛍️  Shop Here",
        f"📊  Owner Dashboard{lock_indicator}",
    ])

    with tab_customer:
        customer_view(inventory)

    with tab_owner:
        owner_view()


if __name__ == "__main__":
    main()
