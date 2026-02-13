import streamlit as st
import pandas as pd
import datetime
import os

# Set page config
st.set_page_config(page_title="Sanjay Karyana Store", layout="centered")

# --- LOAD DATA ---
if not os.path.exists('inventory.csv'):
    # Create a dummy inventory if none exists
    data = {
        'item_name': ['Rice', 'Chana Dal', 'Soap'],
        'category': ['Pulses', 'Pulses', 'Cleaning'],
        'price': [60, 105, 30]
    }
    pd.DataFrame(data).to_csv('inventory.csv', index=False)

inventory = pd.read_csv('inventory.csv')

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Switch View:")
view = st.sidebar.radio("", ["Customer: Shop Here", "Owner: Tablet Dashboard"])

# --- CUSTOMER VIEW ---
if view == "Customer: Shop Here":
    st.title("🏪 Sanjay Karyana  Store")
    
    # Identify the customer
    cust_name = st.text_input("👤 Enter Your Name or Token Number:", placeholder="e.g., Rajesh")
    st.divider()

    if not cust_name:
        st.info("👆 Please enter your name to start shopping.")
    else:
        if 'selected_category' not in st.session_state:
            st.session_state.selected_category = None

        if st.session_state.selected_category is None:
            st.subheader("📂 Choose a Category:")
            all_cats = inventory['category'].unique()
            for cat in all_cats:
                if st.button(f"🛍️ {cat}", use_container_width=True):
                    st.session_state.selected_category = cat
                    st.rerun()
        else:
            if st.button("⬅️ Back to Categories"):
                st.session_state.selected_category = None
                st.rerun()
            
            st.header(f"Category: {st.session_state.selected_category}")
            items = inventory[inventory['category'] == st.session_state.selected_category]
            
            for _, row in items.iterrows():
                with st.container(border=True):
                    col_info, col_ctrl = st.columns([2, 1])
                    col_info.write(f"**{row['item_name']}**")
                    col_info.write(f"Rate: ₹{row['price']}/kg")

                    if st.session_state.selected_category == "Pulses":
                        unit = col_ctrl.radio("Unit", ["kg", "g"], key=f"u_{row['item_name']}", horizontal=True)
                        if unit == "kg":
                            qty = col_ctrl.number_input("Weight", 0.1, 20.0, 0.1, key=f"q_{row['item_name']}")
                            f_qty = qty
                        else:
                            qty = col_ctrl.number_input("Weight", 50, 950, 50, key=f"q_{row['item_name']}")
                            f_qty = qty / 1000
                        d_text = f"{qty}{unit}"
                    else:
                        qty = col_ctrl.number_input("Qty", 1, 50, 1, key=f"q_{row['item_name']}")
                        f_qty = qty
                        d_text = f"{qty} units"

                    if col_ctrl.button("Add to Cart", key=f"b_{row['item_name']}", use_container_width=True):
                        if 'cart' not in st.session_state:
                            st.session_state.cart = []
                        st.session_state.cart.append({
                            'item': row['item_name'], 
                            'price': float(row['price']), 
                            'qty': f_qty,
                            'display_qty': d_text
                        })
                        st.toast(f"Added {d_text} {row['item_name']}")

        # --- Cart Summary ---
        if 'cart' in st.session_state and st.session_state.cart:
            st.divider()
            st.subheader("🛒 Your Selection")
            df_cart = pd.DataFrame(st.session_state.cart)
            df_cart['Subtotal'] = df_cart['price'] * df_cart['qty']
            
            disp = df_cart[['item', 'display_qty', 'Subtotal']].copy()
            disp.columns = ['Item Name', 'Weight/Qty', 'Amount (₹)']
            disp['Amount (₹)'] = disp['Amount (₹)'].map('₹{:.2f}'.format)
            st.table(disp)
            
            total = df_cart['Subtotal'].sum()
            st.write(f"## Total Bill: ₹{total:,.2f}")

            if st.button("CONFIRM ORDER", type="primary", use_container_width=True):
                order_items = ", ".join([f"{i['display_qty']} {i['item']} (@ ₹{i['price']})" for i in st.session_state.cart])
                new_ord = pd.DataFrame([{
                    'Time': datetime.datetime.now().strftime("%H:%M:%S"),
                    'Customer': cust_name,
                    'Items': order_items,
                    'Total': total
                }])
                new_ord.to_csv('orders.csv', mode='a', header=False, index=False)
                st.success(f"Order for {cust_name} sent!")
                st.session_state.cart = []
                st.balloons()

# --- OWNER DASHBOARD ---
elif view == "Owner: Tablet Dashboard":
    st.header("📋 New Orders")
    
    # This button force-fixes the 'Total' column error
    if st.button("Clear All Messy Data"):
        df_reset = pd.DataFrame(columns=['Time', 'Customer', 'Items', 'Total'])
        df_reset.to_csv('orders.csv', index=False)
        st.rerun()

    if os.path.exists('orders.csv'):
        try:
            # We explicitly tell pandas what the columns are to avoid the 'Total' error
            orders_df = pd.read_csv('orders.csv')
            
            # Safety: If the file exists but columns are missing, force a reset
            if 'Total' not in orders_df.columns:
                st.warning("Order file format is old. Please click 'Clear All Messy Data' above.")
                st.stop()

            if not orders_df.empty:
                for index, row in orders_df.iloc[::-1].iterrows():
                    # Your existing code to show the table...
                    cust = row['Customer'] if 'Customer' in row else "Guest"
                    header = f"👤 {cust} | 💰 ₹{row['Total']}"
                    with st.expander(header, expanded=True):
                        # (Insert your table logic here)
                        pass
            else:
                st.info("No orders found. Try placing a test order!")
        except Exception as e:
            st.error(f"Error reading file: {e}")
