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
    st.title("Welcome To Sanjay Karyana Store")
    st.divider()

    # 1. Initialize 'selected_category' in session state if it doesn't exist
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None

    # 2. If no category is selected, show the "Main Menu"
    if st.session_state.selected_category is None:
        st.subheader("📂 Choose a Category to Start:")
        
        all_categories = inventory['category'].unique()
        
        # Display categories as large buttons
        for cat in all_categories:
            if st.button(f"🛍️ {cat}", use_container_width=True, key=f"main_{cat}"):
                st.session_state.selected_category = cat
                st.rerun()

    # 3. If a category IS selected, show the items in that category
    else:
        col_back, col_title = st.columns([1, 3])
        if col_back.button("⬅️ Back"):
            st.session_state.selected_category = None
            st.rerun()
            
        st.header(f"Category: {st.session_state.selected_category}")
        
        # Filter and display items
        items_to_show = inventory[inventory['category'] == st.session_state.selected_category]
        
        for _, row in items_to_show.iterrows():
           # 3. If a category IS selected, show the items in that category
        else:
            col_back, col_title = st.columns([1, 3])
            if col_back.button("⬅️ Back"):
                st.session_state.selected_category = None
                st.rerun()
                
            st.header(f"Category: {st.session_state.selected_category}")
            
            # Filter and display items
            items_to_show = inventory[inventory['category'] == st.session_state.selected_category]
            
            for _, row in items_to_show.iterrows():
                with st.container(border=True):
                    col_info, col_controls = st.columns([2, 1])
                    
                    col_info.write(f"**{row['item_name']}**")
                    col_info.write(f"Rate: ₹{row['price']}/kg")

                    # UNIT SWITCHER LOGIC
                    if st.session_state.selected_category == "Pulses":
                        # Customer chooses kg or g
                        unit = col_controls.radio("Unit", ["kg", "g"], key=f"u_{row['item_name']}", horizontal=True)
                        
                        if unit == "kg":
                            qty = col_controls.number_input("Weight", min_value=0.1, max_value=20.0, step=0.1, key=f"q_{row['item_name']}")
                            final_qty = qty
                        else:
                            qty = col_controls.number_input("Weight", min_value=50, max_value=950, step=50, key=f"q_{row['item_name']}")
                            final_qty = qty / 1000  # MATH: Convert grams to kg for the bill
                            
                        display_text = f"{qty}{unit}"
                    else:
                        # For other items like Biscuits/Soap
                        qty = col_controls.number_input("Qty", min_value=1, max_value=50, step=1, key=f"q_{row['item_name']}")
                        final_qty = qty
                        display_text = f"{qty} units"

                    if col_controls.button("Add to Cart", key=f"b_{row['item_name']}", use_container_width=True):
                        if 'cart' not in st.session_state:
                            st.session_state.cart = []
                        
                        st.session_state.cart.append({
                            'item': row['item_name'], 
                            'price': float(row['price']), 
                            'qty': final_qty,
                            'display_qty': display_text
                        })
                        st.toast(f"Added {display_text} {row['item_name']}")

    # --- Cart Summary (Always visible at the bottom if items exist) ---
    if 'cart' in st.session_state and st.session_state.cart:
        st.divider()
        st.subheader("🛒 Your Selection")
        df_cart = pd.DataFrame(st.session_state.cart)
        df_cart['Subtotal'] = df_cart['price'] * df_cart['qty']
        st.table(df_cart[['item', 'qty', 'Subtotal']])
        
        total_bill = df_cart['Subtotal'].sum()
        st.write(f"## Total Bill: ₹{total_bill}")

        if st.button("CONFIRM ORDER", type="primary", use_container_width=True):
            new_order = pd.DataFrame([{
                'Time': datetime.datetime.now().strftime("%H:%M:%S"),
                'Items': ", ".join([f"{i['qty']}x {i['item']}" for i in st.session_state.cart]),
                'Total': total_bill
            }])
            new_order.to_csv('orders.csv', mode='a', header=False, index=False)
            st.success("Order Sent! Please wait at the counter.")
            st.session_state.cart = []
            st.balloons() # Added a fun celebration effect!

elif view == "Owner: Tablet Dashboard":
    st.header("📋 New Orders")
    
    if st.button("🔄 Refresh Orders"):
        st.rerun()

    if os.path.exists('orders.csv'):
        orders_df = pd.read_csv('orders.csv')
        if not orders_df.empty:
            # We will loop through each order to show a separate table for each one
            for index, row in orders_df.iloc[::-1].iterrows():
                with st.expander(f"Order at {row['Time']} - Total: ₹{row['Total']}", expanded=True):
                    # Convert the text string back into a list for the table
                    item_list = row['Items'].split(", ")
                    
                    # Create a clean table for this specific order
                    order_data = []
                    for item in item_list:
                        qty, name = item.split("x ", 1)
                        order_data.append({"Quantity": qty, "Product Name": name})
                    
                    st.table(order_data)
            
            st.divider()
            if st.button("🗑️ Clear All Orders"):
                pd.DataFrame(columns=['Time', 'Items', 'Total']).to_csv('orders.csv', index=False)
                st.rerun()
        else:
            st.info("No pending orders.")
