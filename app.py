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
    st.title("Sanjay Karyana  Store")
    
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
            all_categories = inventory['category'].unique()
            for cat in all_categories:
                if st.button(f"🛍️ {cat}", use_container_width=True, key=f"main_{cat}"):
                    st.session_state.selected_category = cat
                    st.rerun()
        else:
            if st.button("⬅️ Back to Categories"):
                st.session_state.selected_category = None
                st.rerun()
            
            st.header(f"Category: {st.session_state.selected_category}")
            items_to_show = inventory[inventory['category'] == st.session_state.selected_category]
            
            for _, row in items_to_show.iterrows():
                with st.container(border=True):
                    col_info, col_controls = st.columns([2, 1])
                    col_info.write(f"**{row['item_name']}**")
                    col_info.write(f"Rate: ₹{row['price']}/kg")

                    if st.session_state.selected_category == "Pulses":
                        unit = col_controls.radio("Unit", ["kg", "g"], key=f"u_{row['item_name']}", horizontal=True)
                        if unit == "kg":
                            qty = col_controls.number_input("Weight", min_value=0.1, max_value=20.0, step=0.1, key=f"q_{row['item_name']}")
                            final_qty = qty
                        else:
                            qty = col_controls.number_input("Weight", min_value=50, max_value=950, step=50, key=f"q_{row['item_name']}")
                            final_qty = qty / 1000
                        display_text = f"{qty}{unit}"
                    else:
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

        # --- Cart Summary (Correctly Indented) ---
        if 'cart' in st.session_state and st.session_state.cart:
            st.divider()
            st.subheader("🛒 Your Selection")
            df_cart = pd.DataFrame(st.session_state.cart)
            df_cart['Subtotal'] = df_cart['price'] * df_cart['qty']
            
            display_df = df_cart[['item', 'display_qty', 'Subtotal']].copy()
            display_df.columns = ['Item Name', 'Weight/Qty', 'Amount (₹)']
            display_df['Amount (₹)'] = display_df['Amount (₹)'].map('₹{:.2f}'.format)
            st.table(display_df)
            
            total_bill = df_cart['Subtotal'].sum()
            st.write(f"## Total Bill: ₹{total_bill:,.2f}")

          if st.button("CONFIRM ORDER", type="primary", use_container_width=True)
                # Check if name was entered
                if cust_name:
                    order_string = ", ".join([f"{i['display_qty']} {i['item']} (@ ₹{i['price']})" for i in st.session_state.cart])
                    
                    # Create the data frame with the 'Customer' column
                    new_order = pd.DataFrame([{
                        'Time': datetime.datetime.now().strftime("%H:%M:%S"),
                        'Customer': cust_name,  # THIS SAVES THE NAME
                        'Items': order_string,
                        'Total': total_bill
                    }])
                    
                    # Save to CSV
                    new_order.to_csv('orders.csv', mode='a', header=False, index=False)
                    
                    st.success(f"Order for {cust_name} sent!")
                    st.session_state.cart = []
                    st.balloons()
                else:
                    st.error("Please enter your name at the top before confirming!")

elif view == "Owner: Tablet Dashboard":
    st.header("📋 New Orders")
    
    if st.button("🔄 Refresh Orders"):
        st.rerun()

    if os.path.exists('orders.csv'):
        try:
            # SAFETY: on_bad_lines='warn' prevents the app from crashing if old rows exist
            orders_df = pd.read_csv('orders.csv', on_bad_lines='warn')
            
            if not orders_df.empty:
             for index, row in orders_df.iloc[::-1].iterrows():
                    # Look for 'Customer' column; if empty or missing, then use "Guest"
                    cust_display = row['Customer'] if 'Customer' in row and pd.notna(row['Customer']) else "Guest"
                    
                    header_text = f"👤 {cust_display} | ⏰ {row['Time']} | 💰 ₹{row['Total']}"
                    with st.expander(header_text, expanded=True):
                        # ... rest of your table code ...
                        
                        item_list = str(row['Items']).split(", ")
                        table_data = []
                        
                        for i, entry in enumerate(item_list, 1):
                            parts = entry.split(" ", 1)
                            qty_str = parts[0] if len(parts) > 1 else "1"
                            name_part = parts[1] if len(parts) > 1 else entry
                            
                            if "(@ ₹" in name_part:
                                name, rate_val = name_part.split("(@ ₹", 1)
                                rate = float(rate_val.replace(")", "").strip())
                            else:
                                name, rate = name_part, 0.0

                            try:
                                num_qty = float(qty_str.replace('kg', '').replace('g', ''))
                                if 'g' in qty_str and 'kg' not in qty_str: num_qty /= 1000
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
                        
                        df_display = pd.DataFrame(table_data)
                        st.table(df_display.set_index('S.No'))
                        st.write(f"### 💰 Grand Total: ₹{row['Total']:.2f}")
                
                st.divider()
                if st.button("🗑️ Clear All Orders"):
                    # This resets the file with the correct 4 columns
                    pd.DataFrame(columns=['Time', 'Customer', 'Items', 'Total']).to_csv('orders.csv', index=False)
                    st.rerun()
            else:
                st.info("No pending orders.")
        except Exception as e:
            st.error("Error reading old orders. Please click 'Clear All Orders' below to reset.")
            if st.button("🗑️ Reset Order File Now"):
                pd.DataFrame(columns=['Time', 'Customer', 'Items', 'Total']).to_csv('orders.csv', index=False)
                st.rerun()
             
