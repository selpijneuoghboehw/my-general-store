"""
Sanjay Karyana Store — Single-file Streamlit app
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

# ─── Styling ──────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;600;800&family=Hind:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Hind', sans-serif;
    }

    /* Warm saffron–turmeric palette */
    :root {
        --saffron:   #FF6B00;
        --turmeric:  #F5A623;
        --cream:     #FFF8EE;
        --dark:      #2C1A0E;
        --success:   #2E7D32;
        --card-bg:   #FFFFFF;
        --border:    #F0D9BC;
    }

    .stApp { background-color: var(--cream); }

    /* Top banner */
    .store-header {
        background: linear-gradient(135deg, var(--saffron) 0%, var(--turmeric) 100%);
        padding: 1.2rem 1.8rem;
        border-radius: 16px;
        margin-bottom: 1.4rem;
        box-shadow: 0 4px 18px rgba(255,107,0,.25);
    }
    .store-header h1 {
        font-family: 'Baloo 2', cursive;
        font-weight: 800;
        font-size: 2rem;
        color: #FFFFFF;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .store-header p {
        color: rgba(255,255,255,.85);
        margin: 0;
        font-size: 0.9rem;
    }

    /* Category buttons */
    div[data-testid="column"] .stButton > button {
        background: var(--card-bg);
        border: 2px solid var(--border);
        border-radius: 14px;
        padding: 0.75rem 0.5rem;
        font-family: 'Baloo 2', cursive;
        font-weight: 600;
        font-size: 1rem;
        color: var(--dark);
        width: 100%;
        transition: all .18s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,.06);
    }
    div[data-testid="column"] .stButton > button:hover {
        background: var(--saffron);
        color: #fff;
        border-color: var(--saffron);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(255,107,0,.28);
    }

    /* Confirm order button */
    .confirm-btn > div > button {
        background: linear-gradient(135deg, #2E7D32, #43A047) !important;
        color: white !important;
        border: none !important;
        font-family: 'Baloo 2', cursive !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        border-radius: 12px !important;
        padding: 0.65rem 2.5rem !important;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 14px rgba(46,125,50,.35) !important;
        transition: all .2s !important;
    }
    .confirm-btn > div > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(46,125,50,.4) !important;
    }

    /* Section labels */
    .section-label {
        font-family: 'Baloo 2', cursive;
        font-weight: 700;
        font-size: 1.25rem;
        color: var(--saffron);
        border-left: 4px solid var(--saffron);
        padding-left: 0.6rem;
        margin: 1.2rem 0 0.6rem 0;
    }

    /* Cart total chip */
    .total-chip {
        background: linear-gradient(135deg, var(--saffron), var(--turmeric));
        color: white;
        padding: 0.55rem 1.4rem;
        border-radius: 30px;
        font-family: 'Baloo 2', cursive;
        font-weight: 700;
        font-size: 1.2rem;
        display: inline-block;
        box-shadow: 0 3px 10px rgba(255,107,0,.3);
        margin-top: 0.4rem;
    }

    /* Back button */
    .back-btn button {
        background: transparent !important;
        border: 2px solid var(--border) !important;
        color: var(--saffron) !important;
        font-family: 'Baloo 2', cursive !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--dark) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFF8EE !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-family: 'Baloo 2', cursive !important;
        font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── Customer view ─────────────────────────────────────────────────────────────

def customer_view(inventory: pd.DataFrame):

    # ── Customer name ──────────────────────────────────────────────────────────
    customer_name = st.text_input(
        "👤 Your Name",
        placeholder="Enter your name to start shopping…",
        key="customer_name_input"
    )
    if not customer_name.strip():
        st.info("Please enter your name above to continue shopping.")
        return

    st.success(f"Welcome, **{customer_name.strip()}**! 🛒 Browse categories below.")

    categories = sorted(inventory["category"].unique().tolist())

    # ── Category selection ─────────────────────────────────────────────────────
    if st.session_state.selected_category is None:
        st.markdown('<div class="section-label">🏷️ Select a Category</div>', unsafe_allow_html=True)
        cols = st.columns(min(4, len(categories)))
        for idx, cat in enumerate(categories):
            with cols[idx % len(cols)]:
                cat_icon = {
                    "Pulses": "🌾", "Cleaning": "🧹",
                    "Grocery": "🛒", "Snacks": "🍿"
                }.get(cat, "📦")
                if st.button(f"{cat_icon} {cat}", key=f"cat_{cat}"):
                    st.session_state.selected_category = cat
                    st.rerun()
        st.divider()

    # ── Items in selected category ─────────────────────────────────────────────
    else:
        cat = st.session_state.selected_category
        with st.container():
            back_col, title_col = st.columns([1, 6])
            with back_col:
                if st.button("← Back", key="back_btn"):
                    st.session_state.selected_category = None
                    st.rerun()
            with title_col:
                st.markdown(
                    f'<div class="section-label">🏷️ Category: {cat}</div>',
                    unsafe_allow_html=True
                )

        cat_items = inventory[inventory["category"] == cat].reset_index(drop=True)
        is_pulse  = (cat == "Pulses")

        for _, row in cat_items.iterrows():
            item_name  = row["item_name"]
            item_price = float(row["price"])

            with st.container():
                st.markdown(
                    f"<div style='font-family:Baloo 2,cursive;font-weight:700;"
                    f"font-size:1.05rem;color:#2C1A0E;margin-bottom:4px;'>"
                    f"🛒 {item_name}"
                    f"<span style='font-size:.85rem;color:#888;font-weight:400;margin-left:8px;'>"
                    f"₹{item_price}/{'kg' if is_pulse else 'unit'}</span></div>",
                    unsafe_allow_html=True
                )

                if is_pulse:
                    unit_col, qty_col, btn_col = st.columns([2, 3, 2])
                    with unit_col:
                        unit = st.radio(
                            "Unit", ["kg", "g"],
                            key=f"unit_{item_name}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                    with qty_col:
                        if unit == "kg":
                            qty_val = st.number_input(
                                "Qty", min_value=0.1, max_value=20.0,
                                step=0.1, value=0.5,
                                key=f"qty_{item_name}_kg",
                                label_visibility="collapsed"
                            )
                            qty_kg      = qty_val
                            display_str = f"{qty_val}kg"
                        else:
                            qty_val = st.number_input(
                                "Qty", min_value=50, max_value=950,
                                step=50, value=500,
                                key=f"qty_{item_name}_g",
                                label_visibility="collapsed"
                            )
                            qty_kg      = qty_val / 1000
                            display_str = f"{qty_val}g"
                    with btn_col:
                        amount = round(qty_kg * item_price, 2)
                        if st.button(
                            f"Add  ₹{amount}", key=f"add_{item_name}",
                            use_container_width=True
                        ):
                            st.session_state.cart.append({
                                "item":    item_name,
                                "price":   item_price,
                                "qty_kg":  qty_kg,
                                "display": display_str,
                                "amount":  amount,
                            })
                            st.toast(f"Added {display_str} of {item_name}!", icon="✅")

                else:
                    qty_col, btn_col = st.columns([3, 2])
                    with qty_col:
                        qty_units = st.number_input(
                            "Units", min_value=1, max_value=50,
                            step=1, value=1,
                            key=f"qty_{item_name}_units",
                            label_visibility="collapsed"
                        )
                        display_str = f"{qty_units} units"
                    with btn_col:
                        amount = round(qty_units * item_price, 2)
                        if st.button(
                            f"Add  ₹{amount}", key=f"add_{item_name}",
                            use_container_width=True
                        ):
                            st.session_state.cart.append({
                                "item":    item_name,
                                "price":   item_price,
                                "qty_kg":  qty_units,
                                "display": display_str,
                                "amount":  amount,
                            })
                            st.toast(f"Added {qty_units} × {item_name}!", icon="✅")

                st.divider()

    # ── Cart summary ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">🧺 Your Cart</div>', unsafe_allow_html=True)

    if not st.session_state.cart:
        st.caption("Cart is empty — add items above.")
        return

    cart_rows = [
        {
            "Item Name":     c["item"],
            "Weight / Qty":  c["display"],
            "Amount (₹)":   c["amount"],
        }
        for c in st.session_state.cart
    ]
    cart_df = pd.DataFrame(cart_rows)
    st.dataframe(cart_df, use_container_width=True, hide_index=True)

    total = round(sum(c["amount"] for c in st.session_state.cart), 2)
    st.markdown(
        f'<div class="total-chip">🏷️ Total Bill: ₹{total}</div>',
        unsafe_allow_html=True
    )

    st.markdown("")
    remove_col, confirm_col = st.columns([1, 2])
    with remove_col:
        if st.button("🗑️ Clear Cart", key="clear_cart"):
            st.session_state.cart = []
            st.rerun()

    with confirm_col:
        st.markdown('<div class="confirm-btn">', unsafe_allow_html=True)
        if st.button("✅ CONFIRM ORDER", key="confirm_order", use_container_width=True):
            save_order(customer_name, st.session_state.cart, total)
            st.session_state.cart = []
            st.session_state.selected_category = None
            st.balloons()
            st.success("🎉 Order confirmed! Thank you for shopping at Sanjay Karyana Store.")
        st.markdown("</div>", unsafe_allow_html=True)

# ─── Owner dashboard ───────────────────────────────────────────────────────────

def parse_item_row(item_str: str) -> dict:
    """
    Parse a single item string like '500g Chana Dal (@ ₹105.0)'
    Returns dict with product, quantity, rate, subtotal.
    """
    # Extract rate
    rate_match = re.search(r"@\s*₹([\d.]+)", item_str)
    rate = float(rate_match.group(1)) if rate_match else 0.0

    # Strip the '(@ ₹X)' part to get quantity + product name
    core = re.sub(r"\(@\s*₹[\d.]+\)", "", item_str).strip()

    # Extract leading quantity token (e.g. '500g', '1.5kg', '2')
    qty_match = re.match(r"^([\d.]+(?:kg|g|units)?)\s+(.*)", core)
    if qty_match:
        qty_str  = qty_match.group(1).strip()
        product  = qty_match.group(2).strip()
    else:
        qty_str  = "1"
        product  = core

    # Convert qty to float kg/units
    if "g" in qty_str and "kg" not in qty_str:
        qty_num = float(re.sub(r"[^\d.]", "", qty_str)) / 1000
    elif "kg" in qty_str:
        qty_num = float(re.sub(r"[^\d.]", "", qty_str))
    else:
        qty_num = float(re.sub(r"[^\d.]", "", qty_str) or "1")

    subtotal = round(qty_num * rate, 2)
    return {
        "product":  product,
        "quantity": qty_str,
        "rate":     rate,
        "subtotal": subtotal,
    }


def owner_view():
    st.markdown('<div class="section-label">📊 All Orders</div>', unsafe_allow_html=True)

    # Clear data button
    if st.button("🗑️ Clear All Messy Data", key="clear_orders"):
        clear_orders()
        st.success("All order data cleared.")
        st.rerun()

    orders = load_orders()

    if orders.empty:
        st.info("No orders yet.")
        return

    # Reverse chronological
    orders = orders.iloc[::-1].reset_index(drop=True)

    for idx, order in orders.iterrows():
        customer = str(order.get("Customer", "Guest") or "Guest").strip() or "Guest"
        total    = order.get("Total", "0")
        items_str = str(order.get("Items", ""))
        time_str  = str(order.get("Time",  ""))

        try:
            total_disp = f"₹{float(total):.1f}"
        except (ValueError, TypeError):
            total_disp = "₹?"

        header = f"👤 {customer}   |   💰 Total: {total_disp}   |   🕐 {time_str}"

        with st.expander(header):
            item_parts = [p.strip() for p in items_str.split(",") if p.strip()]

            rows = []
            for sno, part in enumerate(item_parts, start=1):
                parsed = parse_item_row(part)
                rows.append({
                    "S.No":     sno,
                    "Product":  parsed["product"],
                    "Quantity": parsed["quantity"],
                    "Rate":     f"₹{parsed['rate']:.2f}",
                    "Subtotal": f"₹{parsed['subtotal']:.2f}",
                })

            if rows:
                detail_df = pd.DataFrame(rows)
                st.dataframe(detail_df, use_container_width=True, hide_index=True)
            else:
                st.caption("(No item details found)")

# ─── App entry-point ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Sanjay Karyana Store",
        page_icon="🛒",
        layout="wide",
    )
    inject_css()
    init_state()

    inventory = load_inventory()

    # Header banner
    st.markdown("""
    <div class="store-header">
        <h1>🏪 Sanjay Karyana Store</h1>
        <p>Fresh • Trusted • Local  — Est. 1985</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.markdown(
            "<div style='font-family:Baloo 2,cursive;font-size:1.4rem;"
            "font-weight:800;margin-bottom:1rem;'>Navigation</div>",
            unsafe_allow_html=True
        )
        view = st.radio(
            "Choose View",
            ["Customer: Shop Here", "Owner: Tablet Dashboard"],
            key="nav_view",
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Sanjay Karyana Store © 2025")

    if view == "Customer: Shop Here":
        customer_view(inventory)
    else:
        owner_view()


if __name__ == "__main__":
    main()
