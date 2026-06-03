"""
Sanjay Karyana Store — Efficient Edition (v4.0)
Run: streamlit run app.py
"""

import os, re, time
from datetime import datetime

import pandas as pd
import streamlit as st

# ── Constants ──────────────────────────────────────────────────────────────────
INVENTORY_FILE  = "inventory.csv"
ORDERS_FILE     = "orders.csv"
ORDERS_COLS     = ["Time", "Customer", "Items", "Total"]
OWNER_PIN       = "1969"
MAX_ATTEMPTS    = 5
LOCKOUT_SECONDS = 30

CAT_ICONS = {"Pulses": "🌾", "Cleaning": "🧹", "Grocery": "🛒", "Snacks": "🍿"}

SEED_INVENTORY = [
    ("Rice",          "Pulses",   60),  ("Chana Dal",     "Pulses",  105),
    ("Moong Dal",     "Pulses",  120),  ("Masoor Dal",    "Pulses",   95),
    ("Toor Dal",      "Pulses",  110),  ("Soap",          "Cleaning", 30),
    ("Detergent",     "Cleaning", 85),  ("Floor Cleaner", "Cleaning",120),
    ("Sugar",         "Grocery",  45),  ("Salt",          "Grocery",  20),
    ("Tea Powder",    "Grocery", 250),  ("Biscuits",      "Snacks",   40),
    ("Chips",         "Snacks",   20),
]

# ── File I/O ───────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_inventory_cached(mtime: float) -> pd.DataFrame:
    df = pd.read_csv(INVENTORY_FILE)
    df["item_name"] = df["item_name"].fillna("").astype(str).str.strip()
    df["category"]  = df["category"].fillna("Uncategorised").astype(str).str.strip()
    df["price"]     = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    return df[df["item_name"] != ""].reset_index(drop=True)

def load_inventory() -> pd.DataFrame:
    if not os.path.exists(INVENTORY_FILE):
        pd.DataFrame(SEED_INVENTORY, columns=["item_name","category","price"]).to_csv(INVENTORY_FILE, index=False)
    return _load_inventory_cached(os.path.getmtime(INVENTORY_FILE))

@st.cache_data(show_spinner=False)
def _load_orders_cached(mtime: float) -> pd.DataFrame:
    try:
        df = pd.read_csv(ORDERS_FILE, on_bad_lines="skip")
    except Exception:
        df = pd.DataFrame(columns=ORDERS_COLS)
    for col in ORDERS_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[ORDERS_COLS]

def load_orders() -> pd.DataFrame:
    if not os.path.exists(ORDERS_FILE):
        pd.DataFrame(columns=ORDERS_COLS).to_csv(ORDERS_FILE, index=False)
    return _load_orders_cached(os.path.getmtime(ORDERS_FILE))

def save_order(customer: str, cart: list, total: float):
    items_str = ", ".join(f"{r['display']} {r['item']} (@ ₹{r['price']})" for r in cart)
    row = pd.DataFrame([{"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         "Customer": customer.strip() or "Guest",
                         "Items": items_str, "Total": total}])
    pd.concat([load_orders(), row], ignore_index=True).to_csv(ORDERS_FILE, index=False)
    _load_orders_cached.clear()

def save_inventory(df: pd.DataFrame):
    df.to_csv(INVENTORY_FILE, index=False)
    _load_inventory_cached.clear()

def update_order(idx: int, items: list, total: float):
    orders = load_orders()
    orders.at[idx, "Items"] = ", ".join(f"{e['quantity']} {e['product']} (@ ₹{e['rate']})" for e in items)
    orders.at[idx, "Total"] = total
    orders.to_csv(ORDERS_FILE, index=False)
    _load_orders_cached.clear()

def clear_orders():
    pd.DataFrame(columns=ORDERS_COLS).to_csv(ORDERS_FILE, index=False)
    _load_orders_cached.clear()

# ── Session state ──────────────────────────────────────────────────────────────
def init_state():
    defaults = dict(cart=[], selected_category=None, owner_authenticated=False,
                    pin_buffer="", pin_attempts=0, pin_locked_until=0.0,
                    pin_shake=False, pin_message="",
                    editing_order_idx=None, edit_items=[])
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

# ── CSS ────────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg:       #0A0C10; --surface: #121418; --card: #181B22; --raised: #1F2330;
  --accent:   #F6A228; --accent-d:#C4811A; --glow: rgba(246,162,40,.18); --glow2: rgba(246,162,40,.08);
  --green:    #22C55E; --red: #EF4444;
  --t1: #EEF0FF; --t2: #8A91AD; --t3: #4A5070;
  --bdr: rgba(255,255,255,.07); --bdr-a: rgba(246,162,40,.35);
}
html,body,[class*="css"],.stApp { font-family:'DM Sans',sans-serif!important; background:var(--bg)!important; color:var(--t1)!important; }
#MainMenu,footer,header,[data-testid="collapsedControl"],section[data-testid="stSidebar"] { display:none!important; visibility:hidden; }
.block-container { padding-top:1.4rem!important; padding-bottom:3rem!important; max-width:1080px!important; }
::-webkit-scrollbar{width:5px} ::-webkit-scrollbar-track{background:var(--bg)} ::-webkit-scrollbar-thumb{background:var(--raised);border-radius:10px}

/* Header */
.hdr { background:var(--card); border:1px solid var(--bdr-a); border-radius:20px; padding:1.5rem 2rem; margin-bottom:1.6rem; position:relative; overflow:hidden; }
.hdr::before { content:''; position:absolute; top:-50px; right:-50px; width:180px; height:180px; background:radial-gradient(circle,var(--glow),transparent 70%); pointer-events:none; }
.hdr h1 { font-family:'Syne',sans-serif!important; font-weight:800; font-size:1.9rem; color:var(--accent)!important; margin:0 0 3px; letter-spacing:-.5px; text-shadow:0 0 28px var(--glow); }
.hdr p  { color:var(--t2)!important; font-size:.85rem; margin:0; letter-spacing:.8px; text-transform:uppercase; }
.hdr .badge { display:inline-block; background:var(--glow); border:1px solid var(--bdr-a); color:var(--accent); font-size:.7rem; font-weight:600; padding:2px 10px; border-radius:20px; letter-spacing:.5px; margin-top:7px; }

/* Labels */
.lbl { font-family:'Syne',sans-serif; font-weight:700; font-size:1rem; color:var(--t1); margin:1.3rem 0 .7rem; display:flex; align-items:center; gap:8px; }
.lbl::after { content:''; flex:1; height:1px; background:var(--bdr); }

/* Cards */
.cat-card { background:var(--card); border:1px solid var(--bdr); border-radius:16px; padding:1.3rem 1rem; text-align:center; margin-bottom:5px; }
.cat-card .ci { font-size:2.1rem; line-height:1; margin-bottom:.45rem; }
.cat-card .cn { font-family:'Syne',sans-serif; font-weight:700; font-size:.92rem; color:var(--t1); }
.cat-card .cc { font-size:.73rem; color:var(--t3); margin-top:2px; }
.itm-card { background:var(--card); border:1px solid var(--bdr); border-radius:14px; padding:.9rem 1.2rem .35rem; margin-bottom:3px; }
.itm-hdr { display:flex; align-items:baseline; justify-content:space-between; margin-bottom:.45rem; }
.itm-name { font-family:'Syne',sans-serif; font-weight:700; font-size:.97rem; color:var(--t1); }
.itm-tag  { background:var(--glow); border:1px solid var(--bdr-a); color:var(--accent); font-size:.75rem; font-weight:600; padding:2px 9px; border-radius:20px; }

/* Buttons */
.stButton>button { font-family:'DM Sans',sans-serif!important; border-radius:10px!important; transition:all .18s!important; font-weight:500!important; }
.add-btn .stButton>button  { background:#F6A228!important; border:none!important; color:#0A0C10!important; font-weight:700!important; width:100%!important; padding:.48rem .8rem!important; box-shadow:0 3px 12px rgba(246,162,40,.45)!important; }
.add-btn .stButton>button:hover { background:#E09010!important; transform:translateY(-2px)!important; box-shadow:0 6px 20px rgba(246,162,40,.6)!important; }
.back-btn .stButton>button { background:transparent!important; border:1px solid var(--bdr)!important; color:var(--t2)!important; font-size:.83rem!important; padding:.32rem .75rem!important; }
.back-btn .stButton>button:hover { border-color:var(--accent)!important; color:var(--accent)!important; }
.ok-btn .stButton>button   { background:linear-gradient(135deg,var(--green),#16A34A)!important; border:none!important; color:#fff!important; font-family:'Syne',sans-serif!important; font-weight:700!important; font-size:.97rem!important; border-radius:12px!important; width:100%!important; padding:.62rem 1rem!important; box-shadow:0 4px 16px rgba(34,197,94,.2)!important; }
.ok-btn .stButton>button:hover { transform:translateY(-2px)!important; box-shadow:0 8px 22px rgba(34,197,94,.35)!important; }
.del-btn .stButton>button  { background:transparent!important; border:1px solid rgba(239,68,68,.35)!important; color:var(--red)!important; font-size:.86rem!important; width:100%!important; padding:.62rem 1rem!important; border-radius:12px!important; }
.del-btn .stButton>button:hover { background:rgba(239,68,68,.08)!important; border-color:var(--red)!important; }
.inv-save .stButton>button { background:linear-gradient(135deg,var(--accent),var(--accent-d))!important; border:none!important; color:var(--bg)!important; font-weight:700!important; font-size:.93rem!important; border-radius:12px!important; padding:.58rem 1rem!important; box-shadow:0 4px 14px var(--glow)!important; }
.inv-add .stButton>button  { background:var(--raised)!important; border:1px solid var(--bdr-a)!important; color:var(--accent)!important; font-weight:600!important; font-size:.93rem!important; border-radius:12px!important; padding:.58rem 1rem!important; }
.inv-add .stButton>button:hover { background:var(--accent)!important; color:var(--bg)!important; }
.lock-btn .stButton>button { background:transparent!important; border:1px solid var(--bdr-a)!important; color:var(--accent)!important; font-size:.8rem!important; padding:.28rem .85rem!important; border-radius:8px!important; }
.rm-btn .stButton>button   { background:transparent!important; border:1px solid rgba(239,68,68,.3)!important; color:var(--red)!important; font-size:.75rem!important; padding:.18rem .45rem!important; border-radius:7px!important; min-width:30px!important; }
.rm-btn .stButton>button:hover { background:rgba(239,68,68,.1)!important; }
.pin-btn .stButton>button  { background:linear-gradient(135deg,var(--accent),var(--accent-d))!important; border:none!important; color:var(--bg)!important; font-family:'Syne',sans-serif!important; font-weight:800!important; font-size:.97rem!important; border-radius:14px!important; width:100%!important; padding:.62rem 2rem!important; box-shadow:0 4px 16px var(--glow)!important; }

/* Inputs */
.stTextInput input,.stNumberInput input { background:var(--raised)!important; border:1px solid var(--bdr)!important; border-radius:10px!important; color:var(--t1)!important; font-family:'DM Sans',sans-serif!important; }
.stTextInput input:focus,.stNumberInput input:focus { border-color:var(--accent)!important; box-shadow:0 0 0 3px var(--glow2)!important; }
.stTextInput label,.stNumberInput label,.stSelectbox label,.stRadio label { color:var(--t2)!important; font-size:.83rem!important; }
.stNumberInput button { background:var(--raised)!important; border-color:var(--bdr)!important; color:var(--accent)!important; }
.stSelectbox>div>div { background:var(--raised)!important; border:1px solid var(--bdr)!important; border-radius:10px!important; color:var(--t1)!important; }

/* Cart */
.cart-box { background:var(--card); border:1px solid var(--bdr); border-radius:14px; padding:1.1rem 1.3rem; margin:.5rem 0; }
.total-row { background:var(--raised); border:1px solid var(--bdr-a); border-radius:12px; padding:.85rem 1.3rem; display:flex; justify-content:space-between; align-items:center; margin-top:.9rem; }
.total-lbl { font-family:'Syne',sans-serif; font-weight:600; font-size:.97rem; color:var(--t2); }
.total-amt { font-family:'Syne',sans-serif; font-weight:800; font-size:1.45rem; color:var(--accent); text-shadow:0 0 18px var(--glow); }

/* Stats */
.stats { display:flex; gap:12px; margin-bottom:1.3rem; flex-wrap:wrap; }
.stat  { flex:1; min-width:110px; background:var(--card); border:1px solid var(--bdr); border-radius:14px; padding:.9rem 1.1rem; }
.stat .sv { font-family:'Syne',sans-serif; font-weight:800; font-size:1.55rem; color:var(--accent); }
.stat .sl { font-size:.75rem; color:var(--t3); text-transform:uppercase; letter-spacing:.6px; margin-top:2px; }

/* Expander / Tabs */
.stExpander { background:var(--card)!important; border:1px solid var(--bdr)!important; border-radius:14px!important; margin-bottom:9px!important; }
.stExpander:hover { border-color:var(--bdr-a)!important; }
.stExpander summary { font-family:'Syne',sans-serif!important; font-weight:600!important; color:var(--t1)!important; padding:.8rem 1.1rem!important; }
.stExpander [data-testid="stExpanderDetails"] { background:var(--raised)!important; border-top:1px solid var(--bdr)!important; padding:.9rem 1.1rem!important; }
.stDataFrame { border-radius:12px!important; overflow:hidden!important; border:1px solid var(--bdr)!important; }
.stTabs [data-baseweb="tab-list"] { background:var(--card)!important; border:1px solid var(--bdr)!important; border-radius:14px!important; padding:5px 6px!important; gap:4px!important; margin-bottom:1.3rem!important; }
.stTabs [data-baseweb="tab"] { background:transparent!important; border:none!important; border-radius:10px!important; color:var(--t3)!important; font-family:'Syne',sans-serif!important; font-weight:600!important; font-size:.92rem!important; padding:.5rem 1.3rem!important; transition:all .16s!important; }
.stTabs [data-baseweb="tab"]:hover { color:var(--t1)!important; background:var(--raised)!important; }
.stTabs [aria-selected="true"] { background:var(--accent)!important; color:var(--bg)!important; font-weight:700!important; box-shadow:0 2px 10px var(--glow)!important; }
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"] { display:none!important; }
hr { border:none!important; border-top:1px solid var(--bdr)!important; margin:.9rem 0!important; }
[data-testid="stToast"] { background:var(--raised)!important; border:1px solid var(--bdr-a)!important; border-radius:12px!important; }

/* PIN */
.pin-wrap { display:flex; flex-direction:column; align-items:center; padding:1.8rem 1rem 2.2rem; }
.pin-icon  { width:68px; height:68px; background:var(--glow); border:2px solid var(--bdr-a); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.9rem; margin-bottom:1.1rem; box-shadow:0 0 28px var(--glow); }
.pin-title { font-family:'Syne',sans-serif; font-weight:800; font-size:1.4rem; color:var(--t1); margin:0 0 3px; text-align:center; }
.pin-sub   { font-size:.83rem; color:var(--t3); text-align:center; margin-bottom:1.6rem; }
.pin-dots  { display:flex; gap:12px; margin-bottom:.5rem; justify-content:center; }
.pin-dot   { width:17px; height:17px; border-radius:50%; border:2px solid var(--t3); background:transparent; transition:all .16s; }
.pin-dot.filled { background:var(--accent); border-color:var(--accent); box-shadow:0 0 9px var(--glow); }
.pin-dot.error  { background:var(--red);    border-color:var(--red);    box-shadow:0 0 9px rgba(239,68,68,.3); }
.pin-msg-ok   { font-size:.8rem; color:var(--green); text-align:center; min-height:1.2em; margin-bottom:1.1rem; }
.pin-msg-err  { font-size:.8rem; color:var(--red);   text-align:center; min-height:1.2em; margin-bottom:1.1rem; }
.pin-msg-warn { font-size:.8rem; color:var(--accent); text-align:center; min-height:1.2em; margin-bottom:1.1rem; }
.pin-msg-x    { font-size:.8rem; color:transparent;   text-align:center; min-height:1.2em; margin-bottom:1.1rem; }
.lockout-box  { background:rgba(239,68,68,.06); border:1px solid rgba(239,68,68,.28); border-radius:14px; padding:1.1rem 1.5rem; text-align:center; margin:1rem 0; }
.lockout-box .lct { font-family:'Syne',sans-serif; font-weight:700; font-size:.97rem; color:var(--red); margin-bottom:3px; }
.lockout-box .lcm { font-size:.8rem; color:var(--t3); }
.edit-panel { background:var(--bg); border:1px solid var(--bdr-a); border-radius:13px; padding:1rem 1.2rem; margin-top:.7rem; }
.name-banner { background:var(--card); border:1px solid var(--bdr); border-radius:14px; padding:1.2rem 1.5rem; margin-bottom:1.1rem; }
.name-banner p { font-family:'Syne',sans-serif; font-weight:700; font-size:1.05rem; color:var(--t1); margin:0 0 .7rem; }
</style>""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_item_row(s: str) -> dict:
    rate  = float(m.group(1)) if (m := re.search(r"@\s*₹([\d.]+)", s)) else 0.0
    core  = re.sub(r"\(@\s*₹[\d.]+\)", "", s).strip()
    if m2 := re.match(r"^([\d.]+)\s*(kg|g|units)?\s+(.*)", core):
        num, unit, product = m2.group(1), (m2.group(2) or "").strip(), m2.group(3).strip()
    else:
        num, unit, product = "1", "", core
    qty_kg = float(num) / 1000 if unit == "g" else float(num)
    disp   = f"{num}{unit}" if unit in ("kg","g") else (f"{num} units" if unit == "units" else num)
    return {"product": product, "quantity": disp, "rate": rate, "subtotal": round(qty_kg * rate, 2)}

def btn(css_class: str):
    """Context manager shorthand for wrapping buttons in a CSS class div."""
    return st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

def end():
    st.markdown("</div>", unsafe_allow_html=True)

# ── Item row renderer ──────────────────────────────────────────────────────────
def render_item(row: pd.Series, key_prefix: str, is_cart: bool = True):
    name   = str(row["item_name"])
    price  = float(row["price"])
    pulse  = str(row["category"]) == "Pulses"
    unit_l = "per kg" if pulse else "per unit"

    st.markdown(f"""<div class="itm-card">
      <div class="itm-hdr"><span class="itm-name">{name}</span>
      <span class="itm-tag">₹{price:.0f} {unit_l}</span></div></div>""",
      unsafe_allow_html=True)

    if pulse:
        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        with c1:
            unit = st.radio("u", ["kg","g"], key=f"{key_prefix}_u_{name}", horizontal=True, label_visibility="collapsed")
        with c2:
            if unit == "kg":
                qv = st.number_input("q", .1, 20., .5, .1, key=f"{key_prefix}_q_{name}_kg", label_visibility="collapsed")
                qty_kg, disp = qv, f"{qv}kg"
            else:
                qv = st.number_input("q", 50, 950, 500, 50, key=f"{key_prefix}_q_{name}_g",  label_visibility="collapsed")
                qty_kg, disp = qv/1000, f"{qv}g"
        with c3:
            amt = round(qty_kg * price, 2)
            st.markdown(f"<div style='padding:.48rem 0;color:#8A91AD;font-size:.86rem'>= <span style='color:var(--accent);font-weight:700;font-size:.97rem'>₹{amt}</span></div>", unsafe_allow_html=True)
        with c4:
            btn("add-btn")
            if st.button("＋ Add", key=f"{key_prefix}_add_{name}", use_container_width=True):
                _add_to_target(is_cart, name, price, qty_kg, disp, amt)
            end()
    else:
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            qv = st.number_input("u", 1, 50, 1, 1, key=f"{key_prefix}_q_{name}_u", label_visibility="collapsed")
            disp = f"{qv} units"
        with c2:
            amt = round(qv * price, 2)
            st.markdown(f"<div style='padding:.48rem 0;color:#8A91AD;font-size:.86rem'>= <span style='color:var(--accent);font-weight:700;font-size:.97rem'>₹{amt}</span></div>", unsafe_allow_html=True)
        with c3:
            btn("add-btn")
            if st.button("＋ Add", key=f"{key_prefix}_add_{name}", use_container_width=True):
                _add_to_target(is_cart, name, price, float(qv), disp, amt)
            end()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

def _add_to_target(is_cart, name, price, qty_kg, disp, amt):
    if is_cart:
        st.session_state.cart.append({"item": name, "price": price, "qty_kg": qty_kg, "display": disp, "amount": amt})
        st.toast(f"✅ {disp} of {name} added!")
    else:
        st.session_state.edit_items.append({"product": name, "quantity": disp, "rate": price, "subtotal": amt})
        st.toast(f"✅ {disp} of {name} added to order!")
    st.rerun()

# ── PIN screen ─────────────────────────────────────────────────────────────────
def pin_lock_screen() -> bool:
    if st.session_state.owner_authenticated:
        return True

    now, locked_until = time.time(), st.session_state.pin_locked_until
    if now < locked_until:
        secs = int(locked_until - now) + 1
        _, mid, _ = st.columns([1,2,1])
        with mid:
            st.markdown(f"""<div class="pin-wrap"><div class="pin-icon">🔐</div>
              <div class="pin-title">Owner Dashboard</div>
              <div class="pin-sub">Enter your 4-digit PIN to continue</div>
              <div class="lockout-box"><div class="lct">🚫 Too many wrong attempts</div>
              <div class="lcm">Wait <strong style="color:var(--red)">{secs}s</strong> before trying again.</div></div>
            </div>""", unsafe_allow_html=True)
        time.sleep(1); st.rerun()
        return False

    buf, pin_len = st.session_state.pin_buffer, len(OWNER_PIN)
    dot_cls      = "error" if st.session_state.pin_shake else "filled"
    dots         = "".join(f'<div class="pin-dot {dot_cls}"></div>' if i < len(buf) else '<div class="pin-dot"></div>' for i in range(pin_len))

    msg, msg_cls = st.session_state.pin_message, "pin-msg-x"
    if msg.startswith("✅"): msg_cls = "pin-msg-ok"
    elif msg.startswith("❌"): msg_cls = "pin-msg-err"
    elif msg.startswith("⚠"):  msg_cls = "pin-msg-warn"

    _, mid, _ = st.columns([1,2,1])
    with mid:
        st.markdown(f"""<div class="pin-wrap"><div class="pin-icon">🔐</div>
          <div class="pin-title">Owner Dashboard</div>
          <div class="pin-sub">Enter your 4-digit PIN to continue</div>
          <div class="pin-dots">{dots}</div>
          <div class="{msg_cls}">{msg or "&nbsp;"}</div></div>""", unsafe_allow_html=True)

        for row in [["1","2","3"],["4","5","6"],["7","8","9"],["__","0","⌫"]]:
            cols = st.columns(3)
            for col, key in zip(cols, row):
                with col:
                    if key == "__":
                        pass
                    elif key == "⌫":
                        if st.button("⌫", key="pin_del", use_container_width=True):
                            st.session_state.update(pin_buffer=buf[:-1], pin_shake=False, pin_message=""); st.rerun()
                    else:
                        if st.button(key, key=f"pin_{key}", use_container_width=True):
                            if len(buf) < pin_len:
                                nb = buf + key
                                st.session_state.update(pin_buffer=nb, pin_shake=False, pin_message="")
                                if len(nb) == pin_len:
                                    if nb == OWNER_PIN:
                                        st.session_state.update(owner_authenticated=True, pin_buffer="", pin_attempts=0,
                                                                pin_message="✅ Access granted", pin_shake=False)
                                    else:
                                        st.session_state.pin_attempts += 1
                                        rem = MAX_ATTEMPTS - st.session_state.pin_attempts
                                        st.session_state.pin_shake  = True
                                        st.session_state.pin_buffer = ""
                                        if rem <= 0:
                                            st.session_state.update(pin_locked_until=time.time()+LOCKOUT_SECONDS,
                                                                    pin_attempts=0, pin_message=f"⚠ Locked for {LOCKOUT_SECONDS}s")
                                        else:
                                            st.session_state.pin_message = f"❌ Wrong PIN — {rem} attempt{'s' if rem!=1 else ''} left"
                                st.rerun()

        if st.session_state.pin_attempts > 0:
            st.markdown(f"<div style='text-align:center;font-size:.73rem;color:var(--t3);margin-top:.35rem'>⚠ {st.session_state.pin_attempts}/{MAX_ATTEMPTS} failed</div>", unsafe_allow_html=True)
    return False

# ── Customer view ──────────────────────────────────────────────────────────────
def customer_view(inv: pd.DataFrame):
    st.markdown('<div class="name-banner"><p>👤 Who is shopping today?</p></div>', unsafe_allow_html=True)
    name = st.text_input("Name", placeholder="Enter your name to start shopping…", label_visibility="collapsed")
    if not name.strip():
        st.markdown("<small>Please enter your name above to browse the store.</small>", unsafe_allow_html=True)
        return

    st.markdown(f"<div style='font-family:Syne,sans-serif;font-size:.88rem;color:var(--t2);margin-bottom:.35rem'>Welcome, <span style='color:var(--accent);font-weight:700'>{name.strip()}</span> ✨</div>", unsafe_allow_html=True)

    # Search
    search = st.text_input("Search", placeholder="🔍  Search items e.g. Rice, Soap, Dal…", label_visibility="collapsed")

    if search.strip():
        q       = search.strip().lower()
        matched = inv[inv["item_name"].str.lower().str.contains(q, na=False)]
        st.markdown(f'<div class="lbl">🔍 Results for "{search.strip()}"</div>', unsafe_allow_html=True)
        if matched.empty:
            st.markdown(f"<small>No items match '{search.strip()}'.</small>", unsafe_allow_html=True)
        else:
            for _, row in matched.iterrows():
                render_item(row, "cs", is_cart=True)

    elif st.session_state.selected_category is None:
        cats = sorted(inv["category"].dropna().unique())
        st.markdown('<div class="lbl">Browse Categories</div>', unsafe_allow_html=True)
        cols = st.columns(min(4, len(cats)))
        for i, cat in enumerate(cats):
            icon, cnt = CAT_ICONS.get(cat,"📦"), len(inv[inv["category"]==cat])
            with cols[i % len(cols)]:
                st.markdown(f'<div class="cat-card"><div class="ci">{icon}</div><div class="cn">{cat}</div><div class="cc">{cnt} items</div></div>', unsafe_allow_html=True)
                if st.button("Shop →", key=f"cat_{cat}", use_container_width=True):
                    st.session_state.selected_category = cat; st.rerun()
    else:
        cat  = st.session_state.selected_category
        c1, c2 = st.columns([1,7])
        with c1:
            btn("back-btn")
            if st.button("← Back", key="back"):
                st.session_state.selected_category = None; st.rerun()
            end()
        with c2:
            st.markdown(f'<div class="lbl">{CAT_ICONS.get(cat,"📦")} {cat}</div>', unsafe_allow_html=True)
        for _, row in inv[inv["category"]==cat].iterrows():
            render_item(row, "cb", is_cart=True)

    # Cart
    st.markdown("---")
    cart = st.session_state.cart
    st.markdown(f'<div class="lbl">🧺 Cart{"" if not cart else f" ({len(cart)} items)"}</div>', unsafe_allow_html=True)

    if not cart:
        st.markdown("<small>Your cart is empty — add items from a category above.</small>", unsafe_allow_html=True)
        return

    st.markdown('<div class="cart-box">', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"Item": c["item"], "Qty": c["display"], "₹": c["amount"]} for c in cart]),
                 use_container_width=True, hide_index=True)
    total = round(sum(c["amount"] for c in cart), 2)
    st.markdown(f'<div class="total-row"><span class="total-lbl">Grand Total</span><span class="total-amt">₹{total}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1,2])
    with c1:
        btn("del-btn")
        if st.button("🗑️ Clear Cart", key="clr_cart", use_container_width=True):
            st.session_state.cart = []; st.rerun()
        end()
    with c2:
        btn("ok-btn")
        if st.button("✅  CONFIRM ORDER", key="confirm", use_container_width=True):
            save_order(name, cart, total)
            st.session_state.cart, st.session_state.selected_category = [], None
            st.balloons()
            st.success("🎉 Order placed! Thank you for shopping at Sanjay Karyana Store.")
        end()

# ── Inventory Manager ──────────────────────────────────────────────────────────
def inventory_manager():
    inv = load_inventory()

    # Update prices
    st.markdown('<div class="lbl">✏️ Update Prices</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:var(--t3)'>Edit prices then click <b style='color:var(--accent)'>Save All Changes</b>.</small><div style='height:8px'></div>", unsafe_allow_html=True)

    updated = []
    for cat in sorted(inv["category"].dropna().unique()):
        st.markdown(f"<div style='font-family:Syne,sans-serif;font-weight:700;font-size:.78rem;color:var(--t3);text-transform:uppercase;letter-spacing:1px;margin:.9rem 0 .35rem'>{CAT_ICONS.get(cat,'📦')} {cat}</div>", unsafe_allow_html=True)
        for _, row in inv[inv["category"]==cat].iterrows():
            c1, c2 = st.columns([3,1])
            with c1:
                st.markdown(f"<div style='font-size:.93rem;color:var(--t1);padding:.42rem 0;border-bottom:1px solid var(--bdr)'>{row['item_name']}</div>", unsafe_allow_html=True)
            with c2:
                np_ = st.number_input("p", 0., value=float(row["price"]), step=.5, key=f"ip_{row['item_name']}", label_visibility="collapsed")
            updated.append({"item_name": row["item_name"], "category": cat, "price": np_})

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    btn("inv-save")
    if st.button("💾  Save All Price Changes", key="save_prices", use_container_width=True):
        save_inventory(pd.DataFrame(updated))
        st.success("✅ Prices updated!"); st.rerun()
    end()

    st.markdown("---")

    # Add item
    st.markdown('<div class="lbl">➕ Add New Item</div>', unsafe_allow_html=True)
    cats = sorted(inv["category"].dropna().unique().tolist())
    c1, c2 = st.columns(2)
    new_name  = c1.text_input("Item Name", placeholder="e.g. Urad Dal", key="ni_name")
    new_price = c2.number_input("Price (₹)", 0., value=50., step=.5, key="ni_price")
    c3, c4 = st.columns(2)
    cat_sel = c3.selectbox("Category", cats + ["➕ New Category…"], key="ni_cat")
    new_cat = c4.text_input("New Category Name", placeholder="e.g. Dairy", key="ni_newcat") if cat_sel == "➕ New Category…" else cat_sel
    final_cat = new_cat.strip() if cat_sel == "➕ New Category…" else cat_sel

    btn("inv-add")
    if st.button("➕  Add Item to Inventory", key="add_item", use_container_width=True):
        if not new_name.strip():             st.error("Please enter an item name.")
        elif not final_cat:                  st.error("Please enter a category name.")
        elif new_name.strip().lower() in inv["item_name"].str.lower().tolist():
            st.warning(f"'{new_name.strip()}' already exists.")
        else:
            save_inventory(pd.concat([inv, pd.DataFrame([{"item_name": new_name.strip(), "category": final_cat, "price": new_price}])], ignore_index=True))
            st.success(f"✅ '{new_name.strip()}' added!"); st.rerun()
    end()

    st.markdown("---")

    # Remove item
    st.markdown('<div class="lbl">🗑️ Remove Item</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3,1])
    to_del = c1.selectbox("Item", ["— select —"] + inv["item_name"].tolist(), key="del_sel", label_visibility="collapsed")
    with c2:
        btn("del-btn")
        if st.button("🗑️ Remove", key="del_item", use_container_width=True):
            if to_del == "— select —": st.error("Select an item first.")
            else:
                save_inventory(inv[inv["item_name"] != to_del].reset_index(drop=True))
                st.success(f"✅ '{to_del}' removed."); st.rerun()
        end()

    st.markdown("---")
    st.markdown('<div class="lbl">📦 Current Inventory</div>', unsafe_allow_html=True)
    disp = inv[["item_name","category","price"]].copy()
    disp.columns = ["Item","Category","Price (₹)"]
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ── Owner Dashboard ────────────────────────────────────────────────────────────
def owner_view():
    if not pin_lock_screen():
        return

    _, lc = st.columns([8,1])
    with lc:
        btn("lock-btn")
        if st.button("🔒 Lock", key="lock"):
            st.session_state.update(owner_authenticated=False, pin_buffer="", pin_message="", pin_shake=False); st.rerun()
        end()

    orders = load_orders()
    rev    = orders["Total"].astype(float).sum() if not orders.empty else 0.0
    custs  = orders["Customer"].nunique() if not orders.empty else 0

    st.markdown(f"""<div class="stats">
      <div class="stat"><div class="sv">{len(orders)}</div><div class="sl">Total Orders</div></div>
      <div class="stat"><div class="sv">₹{rev:,.0f}</div><div class="sl">Revenue</div></div>
      <div class="stat"><div class="sv">{custs}</div><div class="sl">Customers</div></div>
    </div>""", unsafe_allow_html=True)

    t1, t2 = st.tabs(["📋  Order History", "📦  Manage Inventory"])

    with t1:
        st.markdown('<div class="lbl">📋 Order History</div>', unsafe_allow_html=True)
        btn("del-btn")
        if st.button("🗑️  Clear All Orders", key="clr_orders"):
            clear_orders(); st.session_state.update(editing_order_idx=None, edit_items=[]); st.success("Cleared."); st.rerun()
        end()

        if orders.empty:
            st.markdown("<small>No orders yet.</small>", unsafe_allow_html=True)
        else:
            inv = load_inventory()
            for _, order in orders.iloc[::-1].reset_index().iterrows():
                oi  = int(order["index"])
                cst = str(order.get("Customer","Guest") or "Guest").strip() or "Guest"
                tot = order.get("Total","0")
                istr= str(order.get("Items",""))
                t   = str(order.get("Time","—"))
                try: td = f"₹{float(tot):.2f}"
                except: td = "₹—"

                with st.expander(f"👤  {cst}   ·   💰 {td}   ·   🕐 {t}"):
                    parts = [p.strip() for p in istr.split(",") if p.strip()]
                    rows  = [{"S.No": i+1, **{k:v for k,v in parse_item_row(p).items()}} for i,p in enumerate(parts)]
                    if rows:
                        df = pd.DataFrame(rows)
                        df["rate"]     = df["rate"].apply(lambda x: f"₹{x:.2f}")
                        df["subtotal"] = df["subtotal"].apply(lambda x: f"₹{x:.2f}")
                        df.columns     = ["S.No","Product","Qty","Rate","Subtotal"]
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    ec, _ = st.columns([1,5])
                    with ec:
                        btn("inv-add")
                        if st.button("✏️ Edit", key=f"edit_{oi}"):
                            st.session_state.editing_order_idx = oi
                            st.session_state.edit_items = [parse_item_row(p.strip()) for p in istr.split(",") if p.strip()]
                            st.rerun()
                        end()

                    if st.session_state.editing_order_idx == oi:
                        ei = st.session_state.edit_items
                        st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                        st.markdown('<div style="font-family:Syne,sans-serif;font-weight:700;font-size:.93rem;color:var(--accent);margin-bottom:.7rem">✏️ Editing Order</div>', unsafe_allow_html=True)

                        if ei:
                            for idx2, item in enumerate(ei):
                                r1,r2,r3,r4 = st.columns([3,2,2,1])
                                r1.markdown(f"<div style='padding:.38rem 0;font-size:.9rem;font-weight:500'>{item['product']}</div>", unsafe_allow_html=True)
                                r2.markdown(f"<div style='padding:.38rem 0;font-size:.85rem;color:var(--t2)'>{item['quantity']}</div>", unsafe_allow_html=True)
                                r3.markdown(f"<div style='padding:.38rem 0;font-size:.85rem;color:var(--accent)'>₹{item['subtotal']:.2f}</div>", unsafe_allow_html=True)
                                with r4:
                                    btn("rm-btn")
                                    if st.button("✕", key=f"rm_{oi}_{idx2}"):
                                        st.session_state.edit_items.pop(idx2); st.rerun()
                                    end()
                        else:
                            st.markdown("<small style='color:var(--t3)'>No items — add one below.</small>", unsafe_allow_html=True)

                        srch = st.text_input("Search item", placeholder="🔍  Type item name…", key=f"osrch_{oi}", label_visibility="collapsed")
                        if srch.strip():
                            matched = inv[inv["item_name"].str.lower().str.contains(srch.strip().lower(), na=False)]
                            if matched.empty:
                                st.markdown("<small style='color:var(--t3)'>No match.</small>", unsafe_allow_html=True)
                            else:
                                for _, mrow in matched.iterrows():
                                    render_item(mrow, f"oe_{oi}", is_cart=False)

                        new_total = round(sum(x["subtotal"] for x in st.session_state.edit_items), 2)
                        st.markdown(f"<div style='background:var(--raised);border:1px solid var(--bdr-a);border-radius:10px;padding:.55rem 1rem;display:flex;justify-content:space-between;margin:.7rem 0'><span style='color:var(--t2)'>Updated Total</span><span style='color:var(--accent);font-weight:800;font-size:1.05rem'>₹{new_total}</span></div>", unsafe_allow_html=True)

                        sc1, sc2 = st.columns(2)
                        with sc1:
                            btn("ok-btn")
                            if st.button("💾 Save", key=f"sv_{oi}", use_container_width=True):
                                if not st.session_state.edit_items:
                                    st.error("Need at least one item.")
                                else:
                                    update_order(oi, st.session_state.edit_items, new_total)
                                    st.session_state.update(editing_order_idx=None, edit_items=[])
                                    st.success("✅ Order updated!"); st.rerun()
                            end()
                        with sc2:
                            btn("del-btn")
                            if st.button("✕ Cancel", key=f"cn_{oi}", use_container_width=True):
                                st.session_state.update(editing_order_idx=None, edit_items=[]); st.rerun()
                            end()
                        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        inventory_manager()

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Sanjay Karyana Store", page_icon="🛒", layout="wide")
    inject_css()
    init_state()

    inv = load_inventory()

    st.markdown("""<div class="hdr">
      <h1>🏪 Sanjay Karyana Store</h1>
      <p>Fresh &nbsp;·&nbsp; Trusted &nbsp;·&nbsp; Local</p>
      <div class="badge">EST. 2015 &nbsp;·&nbsp; MASHKA</div>
    </div>""", unsafe_allow_html=True)

    lock = " 🔓" if st.session_state.owner_authenticated else " 🔒"
    t_cust, t_owner = st.tabs([f"🛍️  Shop Here", f"📊  Owner Dashboard{lock}"])

    with t_cust:  customer_view(inv)
    with t_owner: owner_view()

if __name__ == "__main__":
    main()
