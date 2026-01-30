import streamlit as st
import pandas as pd
import datetime
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="General Store Agent", layout="wide")

# 1. Load and Clean Data
def load_data():
    # Make sure inventory.csv is uploaded to the same folder on GitHub
    df = pd.read_csv('inventory.csv')
    # This line fixes the ' category' space error from your spreadsheet
    df.columns = df.columns.str.strip()
    return df

inventory = load_data()

# 2. Setup Order Storage
if not os.path.exists('orders.csv'):
    pd.DataFrame(columns=['Time', 'Items', 'Total']).to_csv('orders.csv', index=False)

# Sidebar for switching between Customer and Owner
view = st.sidebar.radio("Switch View:", ["Customer: Shop Here", "Owner: Tablet Dashboard"])

if view == "Customer: Shop Here":
    st.header("🛒 Welcome to Our Store")
    
    if 'cart' not in st.session_state:
        st.session_state.cart = []

    # Display items by category
    categories = inventory['category'].unique()
    for cat in categories:
        st.subheader(f"--- {cat} ---")
        items_in_cat = inventory[inventory['category'] == cat]
        
        for _, row in items_in_cat.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"**{row['item_name']}**")
            col2.write(f"₹{row['price']}")
            
            qty = col3.number_input("Qty", min_value=1, max_value=20, key=f"q_{row['item_name']}")
            
            if col3.button("Add", key=f"b_{row['item_name']}"):
                st.session_state.cart.append({'item': row['item_name'], 'price': row['price'], 'qty': qty})
                st.toast(f"Added {qty} {row['item_name']}")

    # Cart Summary
    if st.session_state.cart:
        st.divider()
        st.subheader("Your Selection")
        df_cart = pd.DataFrame(st.session_state.cart)
        df_cart['Subtotal'] = df_cart['price'] * df_cart['qty']
        st.table(df_cart[['item', 'qty', 'Subtotal']])
        
        total_bill = df_cart['Subtotal'].sum()
        st.write(f"## Total Bill: ₹{total_bill}")

        if st.button("CONFIRM ORDER"):
            new_order = pd.DataFrame([{
                'Time': datetime.datetime.now().strftime("%H:%M:%S"),
                'Items': ", ".join([f"{i['qty']}x {i['item']}" for i in st.session_state.cart]),
                'Total': total_bill
            }])
            new_order.to_csv('orders.csv', mode='a', header=False, index=False)
            st.success("Order Sent! Please wait at the counter.")
            st.session_state.cart = []

elif view == "Owner: Tablet Dashboard":
    st.header("📋 New Orders")
    
    if st.button("🔄 Refresh Orders"):
        st.rerun()

    if os.path.exists('orders.csv'):
        orders_df = pd.read_csv('orders.csv')
        if not orders_df.empty:
            st.dataframe(orders_df.iloc[::-1], use_container_width=True)
            
            if st.button("🗑️ Clear All Orders"):
                pd.DataFrame(columns=['Time', 'Items', 'Total']).to_csv('orders.csv', index=False)
                st.rerun()
        else:
            st.info("No pending orders.")
