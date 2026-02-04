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
    #new line
    
    # NEW: Ask for the customer's name or token number
    cust_name = st.text_input("👤 Enter Your Name :", placeholder="")
    st.divider()

    if not cust_name:
        st.warning("Please enter your name above to start shopping.")
        st.stop() # Prevents them from seeing items until name is entered

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

# --- Cart Summary ---
    if 'cart' in st.session_state and st.session_state.cart:
        st.divider()
        st.subheader("🛒 Your Selection")
        
        df_cart = pd.DataFrame(st.session_state.cart)
        df_cart['Subtotal'] = df_cart['price'] * df_cart['qty']
        
        # This creates the clean table for the customer
        display_df = df_cart[['item', 'display_qty', 'Subtotal']].copy()
        display_df.columns = ['Item Name', 'Weight/Qty', 'Amount (₹)']
        display_df['Amount (₹)'] = display_df['Amount (₹)'].map('₹{:.2f}'.format)
        
        st.table(display_df)
        
        total_bill = df_cart['Subtotal'].sum()
        st.write(f"## Total Bill: ₹{total_bill:,.2f}")

        # FIXED INDENTATION FOR CONFIRM BUTTON
      if st.button("CONFIRM ORDER", type="primary", use_container_width=True):
            order_items_string = ", ".join([f"{i['display_qty']} {i['item']} (@ ₹{i['price']})" for i in st.session_state.cart])
            
            new_order = pd.DataFrame([{
                'Time': datetime.datetime.now().strftime("%H:%M:%S"),
                'Customer': cust_name,  # SAVING THE NAME
                'Items': order_items_string,
                'Total': total_bill
            }])
            
            # Make sure your CSV header is updated to: Time, Customer, Items, Total
            new_order.to_csv('orders.csv', mode='a', header=False, index=False)
            st.success(f"Order for {cust_name} sent!")
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
           # In your Owner Dashboard loop:
for index, row in orders_df.iloc[::-1].iterrows():
    # Now shows Customer Name + Time + Total
    with st.expander(f"👤 {row['Customer']} | ⏰ {row['Time']} | 💰 ₹{row['Total']}", expanded=True):
        # ... rest of your table code ...
                    
                    item_list = str(row['Items']).split(", ")
                    table_data = []
                    
                    for i, entry in enumerate(item_list, 1):
                        parts = entry.split(" ", 1)
                        qty_str = parts[0] if len(parts) > 1 else "1"
                        name_part = parts[1] if len(parts) > 1 else entry
                        
                        if "(@ ₹" in name_part:
                            name, price_val = name_part.split("(@ ₹", 1)
                            rate = float(price_val.replace(")", "").strip())
                        else:
                            name = name_part
                            rate = 0.0

                        try:
                            num_qty = float(qty_str.replace('kg', '').replace('g', ''))
                            if 'g' in qty_str and 'kg' not in qty_str:
                                num_qty = num_qty / 1000
                            subtotal = num_qty * rate
                        except:
                            subtotal = rate

                        table_data.append({
                            "S.No": i,
                            "Product": name.strip(),
                            "Quantity": qty_str,
                            "Rate": f"₹{rate:.2f}",
                            "Subtotal": f"₹{subtotal:.2f}"
                        })
                    
                    # Display the main table
                    df_display = pd.DataFrame(table_data)
                    st.table(df_display.set_index('S.No'))
                    
                    # --- ADDED: GRAND TOTAL DISPLAY ---
                    # This creates a clear summary line at the bottom of the table
                    st.write(f"### 💰 Grand Total to Collect: ₹{row['Total']:.2f}")
            
            st.divider()
            if st.button("🗑️ Clear All Orders"):
                pd.DataFrame(columns=['Time', 'Items', 'Total']).to_csv('orders.csv', index=False)
                st.rerun()
        else:
            st.info("No pending orders yet.")
