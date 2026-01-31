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
   # Filter and display items
        items_to_show = inventory[inventory['category'] == st.session_state.selected_category]
        
        for _, row in items_to_show.iterrows():
            with st.container(border=True):
                col_info, col_controls = st.columns([2, 1])
                
                col_info.write(f"**{row['item_name']}**")
                col_info.write(f"Rate: ₹{row['price']}/kg")

                # --- KG / GRAMS LOGIC ---
                if st.session_state.selected_category == "Pulses":
                    unit = col_controls.radio("Unit", ["kg", "g"], key=f"u_{row['item_name']}", horizontal=True)
                    
                    if unit == "kg":
                        qty = col_controls.number_input("Weight", min_value=0.1, max_value=20.0, step=0.1, key=f"q_{row['item_name']}")
                        final_qty = qty
                    else:
                        qty = col_controls.number_input("Weight", min_value=50, max_value=950, step=50, key=f"q_{row['item_name']}")
                        final_qty = qty / 1000  # Converts grams to kg for the bill
                        
                    display_text = f"{qty}{unit}"
                else:
                    # Logic for non-pulse items (like Soap)
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
        
        # 1. Create the DataFrame from the cart
        df_cart = pd.DataFrame(st.session_state.cart)
        
        # 2. MATH: Calculate subtotal using the hidden raw numbers
        df_cart['Subtotal'] = df_cart['price'] * df_cart['qty']
        
        # 3. FORMATTING: Use the text labels (like '500g') for the table
        # We use 'display_qty' so it shows '500g' instead of '0.5000'
        display_df = df_cart[['item', 'display_qty', 'Subtotal']].copy()
        display_df.columns = ['Item Name', 'Weight/Qty', 'Amount (₹)']
        
        # Format the Amount column to show 2 decimal places (e.g., ₹52.50)
        display_df['Amount (₹)'] = display_df['Amount (₹)'].map('₹{:.2f}'.format)
        
        # FIXED: This now matches the name 'display_df' above
        st.table(display_df)
        
        # 4. TOTAL: Sum the raw numbers for the final bill
        total_bill = df_cart['Subtotal'].sum()
        st.write(f"## Total Bill: ₹{total_bill:,.2f}")

       if st.button("CONFIRM ORDER", type="primary", use_container_width=True):
            # NEW MATH: We now include the price (@ ₹rate) in the string
            order_items_string = ", ".join([
                f"{i['display_qty']} {i['item']} (@ ₹{i['price']})" 
                for i in st.session_state.cart
            ])
            
            new_order = pd.DataFrame([{
                'Time': datetime.datetime.now().strftime("%H:%M:%S"),
                'Items': order_items_string,
                'Total': total_bill
            }])
            
            new_order.to_csv('orders.csv', mode='a', header=False, index=False)
            
            st.success(f"Order for ₹{total_bill:.2f} Sent!")
            st.session_state.cart = []
            st.balloons()
# Added a fun celebration effect!
elif view == "Owner: Tablet Dashboard":
    st.header("📋 New Orders")
    
    if st.button("🔄 Refresh Orders"):
        st.rerun()

    if os.path.exists('orders.csv'):
        orders_df = pd.read_csv('orders.csv')
        
        if not orders_df.empty:
            for index, row in orders_df.iloc[::-1].iterrows():
                with st.expander(f"Order at {row['Time']} — Total Bill: ₹{row['Total']}", expanded=True):
                    
                    item_list = str(row['Items']).split(", ")
                    table_data = []
                    
                    # Loop through items to build the 4-column table
                    for i, entry in enumerate(item_list, 1):
                        # Extract Weight/Qty and Name
                        if "x " in entry:
                            qty, name_part = entry.split("x ", 1)
                        else:
                            parts = entry.split(" ", 1)
                            qty = parts[0] if len(parts) > 1 else "1"
                            name_part = parts[1] if len(parts) > 1 else entry
                        
                        # Extract Price if it exists in the saved string (@ ₹100)
                        if "(@ ₹" in name_part:
                            name, price = name_part.split("(@ ₹", 1)
                            price = "₹" + price.replace(")", "")
                        else:
                            name = name_part
                            price = "N/A"

                        table_data.append({
                            "S.No": i,
                            "Product": name.strip(),
                            "Quantity": qty,
                            "Price/Unit": price
                        })
                    
                    # Display the 4-column table
                    st.table(table_data)
            
            st.divider()
            if st.button("🗑️ Clear All Orders"):
                pd.DataFrame(columns=['Time', 'Items', 'Total']).to_csv('orders.csv', index=False)
                st.rerun()
        else:
            st.info("No pending orders yet.")
