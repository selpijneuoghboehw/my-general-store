"""
Sanjay Karyana Store — Dark Theme Edition
Run: streamlit run app.py
"""

import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st

# ─── Constants ────────────────────────────────────────────────────────────────
INVENTORY_FILE = "inventory.csv"
ORDERS_FILE    = "orders.csv"
ORDERS_COLS    = ["Time", "Customer", "Items", "Total"]

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
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None

# ─── CSS Injection ────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

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
        --text-primary:  #F0F2FF;
        --text-secondary:#9AA0B8;
        --text-muted:    #5A6080;
        --border:        rgba(255,255,255,0.07);
        --border-accent: rgba(245,166,35,0.35);
    }

    html, body, [class*="css"], .stApp {
        font-family: 'DM Sans', sans-serif !important;
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1100px !important;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 10px; }

    .store-header {
        position: relative;
        background: var(--bg-card);
        border: 1px solid var(--border-accent);
        border-radius: 20px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.8rem;
        overflow: hidden;
    }
    .store-header::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 200px; height: 200px;
        background: radial-gradient(circle, var(--accent-glow), transparent 70%);
        pointer-events: none;
    }
    .store-header h1 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 800;
        font-size: 2rem;
        color: var(--accent) !important;
        margin: 0 0 4px 0;
        letter-spacing: -0.5px;
        text-shadow: 0 0 30px var(--accent-glow);
    }
    .store-header p {
        color: var(--text-secondary) !important;
        font-size: 0.88rem;
        margin: 0;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .store-header .badge {
        display: inline-block;
        background: var(--accent-glow);
        border: 1px solid var(--border-accent);
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 20px;
        letter-spacing: 0.5px;
        margin-top: 8px;
    }

    .section-label {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        color: var(--text-primary);
        margin: 1.4rem 0 0.8rem 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-label::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    .name-banner {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
    }
    .name-banner p {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: var(--text-primary);
        margin: 0 0 0.8rem 0;
    }

    .stTextInput input {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'DM Sans', sans-serif !important;
        padding: 0.6rem 1rem !important;
        transition: border-color .2s !important;
    }
    .stTextInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow2) !important;
    }
    .stTextInput label { color: var(--text-secondary) !important; font-size: 0.85rem !important; }

    .stNumberInput input {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stNumberInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow2) !important;
    }
    .stNumberInput button {
        background: var(--bg-elevated) !important;
        border-color: var(--border) !important;
        color: var(--accent) !important;
    }

    .stRadio label { color: var(--text-secondary) !important; font-size: 0.9rem !important; }
    .stRadio [data-testid="stMarkdownContainer"] p { color: var(--text-secondary) !important; }

    .cat-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1.4rem 1rem;
        text-align: center;
        transition: all .22s ease;
        margin-bottom: 6px;
    }
    .cat-card .cat-icon { font-size: 2.2rem; line-height: 1; margin-bottom: 0.5rem; }
    .cat-card .cat-name {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        color: var(--text-primary);
    }
    .cat-card .cat-count { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

    .item-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1rem 1.3rem 0.4rem 1.3rem;
        margin-bottom: 4px;
    }
    .item-card-header {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .item-name {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        color: var(--text-primary);
    }
    .item-price-tag {
        background: var(--accent-glow);
        border: 1px solid var(--border-accent);
        color: var(--accent);
        font-size: 0.78rem;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 20px;
    }

    .stButton > button {
        font-family: 'DM Sans', sans-serif !important;
        border-radius: 10px !important;
        transition: all .2s !important;
        font-weight: 500 !important;
    }

    .add-btn .stButton > button {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-accent) !important;
        color: var(--accent) !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        width: 100% !important;
        padding: 0.45rem 0.8rem !important;
    }
    .add-btn .stButton > button:hover {
        background: var(--accent) !important;
        color: var(--bg-base) !important;
        box-shadow: 0 4px 14px rgba(245,166,35,0.3) !important;
    }

    .back-btn .stButton > button {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        padding: 0.35rem 0.8rem !important;
    }
    .back-btn .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }

    .confirm-btn .stButton > button {
        background: linear-gradient(135deg, var(--green), #16A34A) !important;
        border: none !important;
        color: white !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.3px !important;
        border-radius: 12px !important;
        width: 100% !important;
        padding: 0.65rem 1rem !important;
        box-shadow: 0 4px 18px var(--green-glow) !important;
    }
    .confirm-btn .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(34,197,94,0.35) !important;
    }

    .clear-btn .stButton > button {
        background: transparent !important;
        border: 1px solid rgba(239,68,68,0.4) !important;
        color: var(--red) !important;
        font-size: 0.88rem !important;
        width: 100% !important;
        padding: 0.65rem 1rem !important;
    }
    .clear-btn .stButton > button:hover {
        background: rgba(239,68,68,0.1) !important;
        border-color: var(--red) !important;
    }

    .cart-box {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin: 0.6rem 0;
    }
    .total-row {
        background: var(--bg-elevated);
        border: 1px solid var(--border-accent);
        border-radius: 12px;
        padding: 0.9rem 1.4rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1rem;
    }
    .total-label {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        color: var(--text-secondary);
    }
    .total-amount {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.5rem;
        color: var(--accent);
        text-shadow: 0 0 20px var(--accent-glow);
    }

    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid var(--border) !important;
    }
    [data-testid="stDataFrame"] > div {
        background: var(--bg-card) !important;
        border-radius: 12px !important;
    }

    .stAlert {
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-card) !important;
    }

    .stExpander {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        margin-bottom: 10px !important;
    }
    .stExpander:hover { border-color: var(--border-accent) !important; }
    .stExpander summary {
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        padding: 0.85rem 1.2rem !important;
    }
    .stExpander [data-testid="stExpanderDetails"] {
        background: var(--bg-elevated) !important;
        border-top: 1px solid var(--border) !important;
        padding: 1rem 1.2rem !important;
    }

    section[data-testid="stSidebar"] {
        background: var(--bg-surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
    section[data-testid="stSidebar"] hr { border-color: var(--border) !important; }

    .sidebar-logo {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.3rem;
        color: var(--accent) !important;
        margin-bottom: 4px;
    }
    .sidebar-sub {
        font-size: 0.75rem;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 1.4rem;
    }
    .sidebar-nav-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.5rem;
    }

    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1rem 0 !important;
    }

    .stat-strip {
        display: flex;
        gap: 14px;
        margin-bottom: 1.4rem;
        flex-wrap: wrap;
    }
    .stat-card {
        flex: 1;
        min-width: 120px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1rem 1.2rem;
    }
    .stat-card .stat-val {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.6rem;
        color: var(--accent);
    }
    .stat-card .stat-lbl {
        font-size: 0.78rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-top: 2px;
    }

    .stCaption, small { color: var(--text-muted) !important; }

    [data-testid="stToast"] {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-accent) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── Customer View ─────────────────────────────────────────────────────────────

def customer_view(inventory: pd.DataFrame):

    st.markdown("""
    <div class="name-banner">
        <p>👤 Who is shopping today?</p>
    </div>
    """, unsafe_allow_html=True)

    customer_name = st.text_input(
        "Your Name",
        placeholder="Enter your name to start shopping…",
        key="customer_name_input",
        label_visibility="collapsed",
    )

    if not customer_name.strip():
        st.markdown(
            "<small>Please enter your name above to browse the store.</small>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<div style='font-family:DM Sans,sans-serif;font-size:0.9rem;"
        f"color:#9AA0B8;margin-bottom:0.4rem;'>"
        f"Welcome, <span style='color:#F5A623;font-weight:700'>"
        f"{customer_name.strip()}</span> ✨</div>",
        unsafe_allow_html=True,
    )

    categories = sorted(inventory["category"].unique().tolist())

    # ── Category grid ──────────────────────────────────────────────────────────
    if st.session_state.selected_category is None:
        st.markdown('<div class="section-label">Browse Categories</div>', unsafe_allow_html=True)

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

    # ── Item listing ───────────────────────────────────────────────────────────
    else:
        cat      = st.session_state.selected_category
        icon     = CAT_ICONS.get(cat, "📦")
        is_pulse = (cat == "Pulses")

        top_l, top_r = st.columns([1, 7])
        with top_l:
            st.markdown('<div class="back-btn">', unsafe_allow_html=True)
            if st.button("← Back", key="back_btn"):
                st.session_state.selected_category = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with top_r:
            st.markdown(
                f'<div class="section-label">{icon} {cat}</div>',
                unsafe_allow_html=True,
            )

        cat_items = inventory[inventory["category"] == cat].reset_index(drop=True)

        for _, row in cat_items.iterrows():
            item_name  = str(row["item_name"])
            item_price = float(row["price"])
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
                    unit = st.radio(
                        "Unit", ["kg", "g"],
                        key=f"unit_{item_name}",
                        horizontal=True,
                        label_visibility="collapsed",
                    )
                with c2:
                    if unit == "kg":
                        qty_val = st.number_input(
                            "Qty", min_value=0.1, max_value=20.0,
                            step=0.1, value=0.5,
                            key=f"qty_{item_name}_kg",
                            label_visibility="collapsed",
                        )
                        qty_kg      = qty_val
                        display_str = f"{qty_val}kg"
                    else:
                        qty_val = st.number_input(
                            "Qty", min_value=50, max_value=950,
                            step=50, value=500,
                            key=f"qty_{item_name}_g",
                            label_visibility="collapsed",
                        )
                        qty_kg      = qty_val / 1000
                        display_str = f"{qty_val}g"
                with c3:
                    amount = round(qty_kg * item_price, 2)
                    st.markdown(
                        f"<div style='padding:0.5rem 0;color:#9AA0B8;font-size:0.88rem;'>"
                        f"= <span style='color:#F5A623;font-weight:700;font-size:1rem;'>"
                        f"₹{amount}</span></div>",
                        unsafe_allow_html=True,
                    )
                with c4:
                    st.markdown('<div class="add-btn">', unsafe_allow_html=True)
                    if st.button("＋ Add to Cart", key=f"add_{item_name}", use_container_width=True):
                        st.session_state.cart.append({
                            "item":    item_name,
                            "price":   item_price,
                            "qty_kg":  qty_kg,
                            "display": display_str,
                            "amount":  amount,
                        })
                        st.toast(f"✅ {display_str} of {item_name} added!")
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    qty_units = st.number_input(
                        "Units", min_value=1, max_value=50,
                        step=1, value=1,
                        key=f"qty_{item_name}_units",
                        label_visibility="collapsed",
                    )
                    display_str = f"{qty_units} units"
                with c2:
                    amount = round(qty_units * item_price, 2)
                    st.markdown(
                        f"<div style='padding:0.5rem 0;color:#9AA0B8;font-size:0.88rem;'>"
                        f"= <span style='color:#F5A623;font-weight:700;font-size:1rem;'>"
                        f"₹{amount}</span></div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown('<div class="add-btn">', unsafe_allow_html=True)
                    if st.button("＋ Add to Cart", key=f"add_{item_name}", use_container_width=True):
                        st.session_state.cart.append({
                            "item":    item_name,
                            "price":   item_price,
                            "qty_kg":  qty_units,
                            "display": display_str,
                            "amount":  amount,
                        })
                        st.toast(f"✅ {qty_units} × {item_name} added!")
                    st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Cart ───────────────────────────────────────────────────────────────────
    st.markdown("---")
    cart_count = len(st.session_state.cart)
    st.markdown(
        f'<div class="section-label">🧺 Cart'
        f'{"" if cart_count == 0 else f" ({cart_count} items)"}</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        st.markdown(
            "<small>Your cart is empty — add items from a category above.</small>",
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="cart-box">', unsafe_allow_html=True)
    cart_df = pd.DataFrame([
        {
            "Item":         c["item"],
            "Weight / Qty": c["display"],
            "Amount (₹)":  c["amount"],
        }
        for c in st.session_state.cart
    ])
    st.dataframe(cart_df, use_container_width=True, hide_index=True)

    total = round(sum(c["amount"] for c in st.session_state.cart), 2)
    st.markdown(f"""
    <div class="total-row">
        <span class="total-label">Grand Total</span>
        <span class="total-amount">₹{total}</span>
    </div>
    """, unsafe_allow_html=True)
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

    core      = re.sub(r"\(@\s*₹[\d.]+\)", "", item_str).strip()
    qty_match = re.match(r"^([\d.]+(?:kg|g|units)?)\s+(.*)", core)
    if qty_match:
        qty_str = qty_match.group(1).strip()
        product = qty_match.group(2).strip()
    else:
        qty_str = "1"
        product = core

    if "g" in qty_str and "kg" not in qty_str:
        qty_num = float(re.sub(r"[^\d.]", "", qty_str)) / 1000
    elif "kg" in qty_str:
        qty_num = float(re.sub(r"[^\d.]", "", qty_str))
    else:
        qty_num = float(re.sub(r"[^\d.]", "", qty_str) or "1")

    return {
        "product":  product,
        "quantity": qty_str,
        "rate":     rate,
        "subtotal": round(qty_num * rate, 2),
    }

# ─── Owner Dashboard ───────────────────────────────────────────────────────────

def owner_view():
    orders = load_orders()

    total_orders     = len(orders)
    total_revenue    = 0.0
    unique_customers = 0

    if not orders.empty:
        try:
            total_revenue = orders["Total"].astype(float).sum()
        except Exception:
            total_revenue = 0.0
        unique_customers = orders["Customer"].nunique()

    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-card">
            <div class="stat-val">{total_orders}</div>
            <div class="stat-lbl">Total Orders</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">₹{total_revenue:,.0f}</div>
            <div class="stat-lbl">Total Revenue</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">{unique_customers}</div>
            <div class="stat-lbl">Customers</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">📋 Order History</div>', unsafe_allow_html=True)

    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("🗑️  Clear All Messy Data", key="clear_orders"):
        clear_orders()
        st.success("Order data cleared and reset.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if orders.empty:
        st.markdown(
            "<small>No orders recorded yet. Confirmed orders will appear here.</small>",
            unsafe_allow_html=True,
        )
        return

    orders_rev = orders.iloc[::-1].reset_index(drop=True)

    for _, order in orders_rev.iterrows():
        customer  = str(order.get("Customer", "Guest") or "Guest").strip() or "Guest"
        total_val = order.get("Total", "0")
        items_str = str(order.get("Items", ""))
        time_str  = str(order.get("Time", "—"))

        try:
            total_disp = f"₹{float(total_val):.2f}"
        except (ValueError, TypeError):
            total_disp = "₹—"

        header = f"👤  {customer}   ·   💰 {total_disp}   ·   🕐 {time_str}"

        with st.expander(header):
            item_parts = [p.strip() for p in items_str.split(",") if p.strip()]
            rows = []
            for sno, part in enumerate(item_parts, start=1):
                p = parse_item_row(part)
                rows.append({
                    "S.No":     sno,
                    "Product":  p["product"],
                    "Quantity": p["quantity"],
                    "Rate":     f"₹{p['rate']:.2f}",
                    "Subtotal": f"₹{p['subtotal']:.2f}",
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.caption("(No item details could be parsed)")

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
        <div class="badge">EST. 2015 &nbsp;·&nbsp; Mashka</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="sidebar-logo">🛒 SKS</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Sanjay Karyana Store</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-nav-label">Navigate</div>', unsafe_allow_html=True)

        view = st.radio(
            "View",
            ["Customer: Shop Here", "Owner: Tablet Dashboard"],
            key="nav_view",
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(
            "<small style='color:#5A6080'>v2.0 · Dark Edition<br>© 2025 Sanjay Karyana</small>",
            unsafe_allow_html=True,
        )

    if view == "Customer: Shop Here":
        customer_view(inventory)
    else:
        owner_view()


if __name__ == "__main__":
    main()
