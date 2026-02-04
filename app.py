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
# --- OWNER DASHBOARD ---
elif view == "Owner: Tablet Dashboard":
    st.header("📋 New Orders")
    
    # HARD RESET BUTTON - This will fix the "Order file is messy" error
    if st.button("Clear All Messy Data"):
        # This force-overwrites the file with the correct headers
        df_reset = pd.DataFrame(columns=['Time', 'Customer', 'Items', 'Total'])
        df_reset.to_csv('orders.csv', index=False)
        st.success("File Reset! The 'messy' error should be gone now.")
        st.rerun()

    if st.button("🔄 Refresh Orders"):
        st.rerun()

    if os.path.exists('orders.csv'):
        try:
            # We use 'on_bad_lines' to prevent the parser error you saw
            orders_df = pd.read_csv('orders.csv', on_bad_lines='skip')
            
            if not orders_df.empty:
                for _, row in orders_df.iloc[::-1].iterrows():
                    # Handle rows where customer name might be missing
                    c_name = row['Customer'] if 'Customer' in row else "Guest"
                    header = f"👤 {c_name} |  💰 ₹{row['Total']}"
                    
                    with st.expander(header, expanded=True):
                        items = str(row['Items']).split(", ")
                        table_data = []
                        for i, entry in enumerate(items, 1):
                            # (Parsing logic for your table columns)
                            parts = entry.split(" ", 1)
                            q_str = parts[0] if len(parts) > 1 else "1"
                            name_part = parts[1] if len(parts) > 1 else entry
                            
                            if "(@ ₹" in name_part:
                                name, r_val = name_part.split("(@ ₹", 1)
                                rate = float(r_val.replace(")", "").strip())
                            else:
                                name, rate = name_part, 0.0

                            # (Math for the Packing List)
                            try:
                                n_qty = float(q_str.replace('kg', '').replace('g', ''))
                                if 'g' in q_str and 'kg' not in q_str: n_qty /= 1000
                                sub = n_qty * rate
                            except:
                                sub = rate

                            table_data.append({
                                "S.No": i, 
                                "Product": name.strip(), 
                                "Quantity": q_str, 
                                "Rate": f"₹{rate:.2f}", 
                                "Subtotal": f"₹{sub:.2f}"
                            })
                        
                        st.table(pd.DataFrame(table_data).set_index('S.No'))
                        st.write(f"### 💰 Grand Total: ₹{row['Total']:.2f}")
            else:
                st.info("No pending orders.")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.warning("Click the Red Emergency Reset button above to fix this.")
