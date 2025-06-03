import streamlit as st
import pandas as pd
from datetime import datetime
import os
import database as db # Import your database module
from PIL import Image # For image handling

st.set_page_config(layout="wide")
st.title("🛋️ DYI Furniture Management System (v0.3 - DB Integrated)")

# --- Helper for saving uploaded file ---
def save_uploaded_file(uploaded_file, product_id):
    if uploaded_file is not None:
        # Create a unique filename to avoid overwrites, or use product SKU/ID
        file_extension = os.path.splitext(uploaded_file.name)[1]
        filename = f"product_{product_id}{file_extension}"
        img_path = os.path.join(db.IMAGE_DIR, filename)
        
        # Check if an old image exists and remove it if replacing
        existing_product = db.get_product_by_id(product_id)
        if existing_product and existing_product['ImagePath'] and os.path.exists(existing_product['ImagePath']) and existing_product['ImagePath'] != img_path:
            try:
                os.remove(existing_product['ImagePath'])
            except Exception as e:
                st.warning(f"Could not remove old image {existing_product['ImagePath']}: {e}")

        with open(img_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return img_path
    return None

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
modules = [
    "Dashboard", "Customer Management", "Product Management",
    "Sales Book (Orders)", "Expense Tracking", "Reports" # Simplified list for demo
]
choice = st.sidebar.radio("Go to", modules)

# --- Module Implementations ---

if choice == "Dashboard":
    st.header("📊 Dashboard")
    st.subheader("Key Metrics (Sample)")
    col1, col2, col3, col4 = st.columns(4)
    
    customers = db.get_all_customers()
    products = db.get_all_products()
    orders = db.get_all_orders()
    expenses = db.get_all_expenses()

    col1.metric("Total Customers", len(customers))
    col2.metric("Total Products", len(products))
    
    total_revenue = sum(o['TotalAmount'] for o in orders if o['TotalAmount']) if orders else 0
    col3.metric("Total Sales Revenue", f"${total_revenue:,.2f}")
    
    total_expenses = sum(e['Amount'] for e in expenses if e['Amount']) if expenses else 0
    col4.metric("Total Expenses", f"${total_expenses:,.2f}")

    st.subheader("Recent Orders")
    if orders:
        st.dataframe(db.rows_to_dicts(orders[:5]), use_container_width=True) # Display first 5
    else:
        st.info("No orders yet.")

elif choice == "Customer Management":
    st.header("👥 Customer Management")

    action = st.selectbox("Action", ["View All", "Add New", "Edit Customer", "Delete Customer"])

    if action == "View All":
        st.subheader("Existing Customers")
        search_term_cust = st.text_input("Search Customers (by Name or Email)", key="search_cust")
        customers_list = db.get_all_customers(search_term=search_term_cust)
        if customers_list:
            st.dataframe(db.rows_to_dicts(customers_list), use_container_width=True)
        else:
            st.info("No customers found or added yet.")

    elif action == "Add New":
        st.subheader("Add New Customer")
        with st.form("add_customer_form", clear_on_submit=True):
            name = st.text_input("Customer Name*")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            bill_addr = st.text_area("Billing Address")
            ship_addr = st.text_area("Shipping Address (if different)")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Add Customer")
            if submitted:
                if not name:
                    st.error("Customer Name is required.")
                else:
                    db.add_customer(name, email, phone, bill_addr, ship_addr or bill_addr, notes)
                    st.success("Customer added successfully!")

    elif action == "Edit Customer":
        st.subheader("Edit Customer")
        customers_list = db.get_all_customers()
        customer_options = {f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_list}
        selected_cust_display = st.selectbox("Select Customer to Edit", list(customer_options.keys()))

        if selected_cust_display:
            cust_id_to_edit = customer_options[selected_cust_display]
            customer_data = db.get_customer_by_id(cust_id_to_edit)

            if customer_data:
                with st.form("edit_customer_form"):
                    st.write(f"Editing Customer ID: {customer_data['CustomerID']}")
                    name = st.text_input("Customer Name*", value=customer_data['CustomerName'])
                    email = st.text_input("Email", value=customer_data['Email'])
                    phone = st.text_input("Phone", value=customer_data['Phone'])
                    bill_addr = st.text_area("Billing Address", value=customer_data['BillingAddress'])
                    ship_addr = st.text_area("Shipping Address", value=customer_data['ShippingAddress'])
                    notes = st.text_area("Notes", value=customer_data['Notes'])
                    updated = st.form_submit_button("Update Customer")
                    if updated:
                        if not name:
                            st.error("Customer Name is required.")
                        else:
                            db.update_customer(cust_id_to_edit, name, email, phone, bill_addr, ship_addr, notes)
                            st.success("Customer updated successfully!")
                            st.experimental_rerun() # To refresh selectbox and form
            else:
                st.error("Customer not found.")
    
    elif action == "Delete Customer":
        st.subheader("Delete Customer")
        customers_list = db.get_all_customers()
        customer_options = {f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_list}
        selected_cust_display_del = st.selectbox("Select Customer to Delete", list(customer_options.keys()), key="del_cust_select")

        if selected_cust_display_del:
            cust_id_to_delete = customer_options[selected_cust_display_del]
            st.warning(f"Are you sure you want to delete {selected_cust_display_del}? This action cannot be undone.")
            if st.button("Confirm Delete"):
                try:
                    # You might want to check for related orders before deleting
                    # e.g., if db.get_orders_by_customer_id(cust_id_to_delete): raise Exception("Customer has orders")
                    db.delete_customer(cust_id_to_delete)
                    st.success("Customer deleted successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Could not delete customer. They might have associated records (e.g., orders). Error: {e}")


elif choice == "Product Management":
    st.header("📦 Product Management (Inventory)")
    action_prod = st.selectbox("Action", ["View All", "Add New", "Edit Product", "Delete Product"], key="prod_action")

    if action_prod == "View All":
        st.subheader("Existing Products")
        search_term_prod = st.text_input("Search Products (Name, SKU, Category)", key="search_prod")
        products_list = db.get_all_products(search_term=search_term_prod)
        if products_list:
            # Display basic info, consider adding image display here too
            df_products = pd.DataFrame(db.rows_to_dicts(products_list))
            # Select columns to display, excluding image path if too long
            cols_to_display = [col for col in df_products.columns if col != 'ImagePath']
            st.dataframe(df_products[cols_to_display], use_container_width=True)
            
            # Optional: Image gallery or expander for images
            for prod in products_list:
                if prod['ImagePath'] and os.path.exists(prod['ImagePath']):
                    with st.expander(f"{prod['ProductName']} - Image"):
                        try:
                            image = Image.open(prod['ImagePath'])
                            st.image(image, caption=prod['ProductName'], width=200)
                        except Exception as e:
                            st.warning(f"Could not load image for {prod['ProductName']}: {e}")
        else:
            st.info("No products found or added yet.")

    elif action_prod == "Add New":
        st.subheader("Add New Product")
        with st.form("add_product_form", clear_on_submit=True):
            name = st.text_input("Product Name*")
            sku = st.text_input("SKU (Must be unique)")
            desc = st.text_area("Description")
            category = st.text_input("Category")
            material = st.text_input("Material Type")
            dims = st.text_input("Dimensions (L x W x H)")
            cost = st.number_input("Cost Price ($)", min_value=0.0, format="%.2f")
            sell = st.number_input("Selling Price ($)", min_value=0.0, format="%.2f")
            qty = st.number_input("Quantity In Stock", min_value=0, step=1)
            reorder = st.number_input("Reorder Level", min_value=0, step=1)
            # supplier_id = st.number_input("Supplier ID (Optional)", min_value=0, step=1) # Simplified
            supplier_id = None # For now
            uploaded_image = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"])

            submitted = st.form_submit_button("Add Product")
            if submitted:
                if not name or not sku:
                    st.error("Product Name and SKU are required.")
                else:
                    image_path = None
                    if uploaded_image:
                        # Need a temporary product ID or handle image saving after product creation
                        # For simplicity, let's assume we save image with a placeholder name or after insert
                        # This part needs refinement: save image with actual product ID *after* insert
                        # For now, let's try saving with SKU if unique
                        temp_image_name = f"temp_{sku}_{uploaded_image.name}"
                        temp_path = os.path.join(db.IMAGE_DIR, temp_image_name)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_image.getbuffer())
                        image_path_to_save = temp_path # Will be updated after insert
                    else:
                        image_path_to_save = None

                    try:
                        # Add product without image path first, then update it. This is clunky.
                        # A better way is to insert, get ID, then update image path OR save image with ID.
                        # For now:
                        db.add_product(name, sku, desc, category, material, dims, cost, sell, qty, reorder, supplier_id, image_path_to_save)
                        st.success(f"Product '{name}' added successfully!")
                        # If image_path_to_save was temporary, find the product, get its ID, rename file, update DB
                        # This part is omitted for brevity but is important for robust image handling.
                        # Example:
                        # new_prod = # query product by SKU
                        # if new_prod and image_path_to_save:
                        #    final_img_path = os.path.join(db.IMAGE_DIR, f"product_{new_prod['ProductID']}{os.path.splitext(temp_image_name)[1]}")
                        #    os.rename(image_path_to_save, final_img_path)
                        #    db.update_product_image_path(new_prod['ProductID'], final_img_path)

                    except sqlite3.IntegrityError:
                        st.error(f"SKU '{sku}' already exists. Please use a unique SKU.")
                        if image_path_to_save and os.path.exists(image_path_to_save):
                            os.remove(image_path_to_save) # Clean up temp image
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        if image_path_to_save and os.path.exists(image_path_to_save):
                            os.remove(image_path_to_save)

    elif action_prod == "Edit Product":
        st.subheader("Edit Product")
        products_list = db.get_all_products()
        product_options = {f"{p['ProductName']} (SKU: {p['SKU']}, ID: {p['ProductID']})": p['ProductID'] for p in products_list}
        selected_prod_display = st.selectbox("Select Product to Edit", list(product_options.keys()), key="edit_prod_select")

        if selected_prod_display:
            prod_id_to_edit = product_options[selected_prod_display]
            product_data = db.get_product_by_id(prod_id_to_edit)

            if product_data:
                with st.form("edit_product_form"):
                    st.write(f"Editing Product ID: {product_data['ProductID']}")
                    name = st.text_input("Product Name*", value=product_data['ProductName'])
                    sku = st.text_input("SKU (Must be unique)", value=product_data['SKU'])
                    desc = st.text_area("Description", value=product_data['Description'])
                    # ... (all other fields like in add form) ...
                    category = st.text_input("Category", value=product_data.get('Category', ''))
                    material = st.text_input("Material Type", value=product_data.get('MaterialType', ''))
                    dims = st.text_input("Dimensions", value=product_data.get('Dimensions', ''))
                    cost = st.number_input("Cost Price ($)", value=float(product_data.get('CostPrice', 0.0)), format="%.2f")
                    sell = st.number_input("Selling Price ($)", value=float(product_data.get('SellingPrice', 0.0)), format="%.2f")
                    qty = st.number_input("Quantity In Stock", value=int(product_data.get('QuantityInStock', 0)), step=1)
                    reorder = st.number_input("Reorder Level", value=int(product_data.get('ReorderLevel', 0)), step=1)
                    supplier_id = None # Simplified

                    st.write("Current Image:")
                    current_image_path = product_data['ImagePath']
                    if current_image_path and os.path.exists(current_image_path):
                        try:
                            image = Image.open(current_image_path)
                            st.image(image, width=150)
                        except Exception as e:
                            st.warning(f"Could not load current image: {e}")
                    else:
                        st.text("No image.")
                    
                    new_uploaded_image = st.file_uploader("Upload New Image (Optional - will replace old)", type=["png", "jpg", "jpeg"], key="edit_img_upload")

                    updated = st.form_submit_button("Update Product")
                    if updated:
                        if not name or not sku:
                            st.error("Product Name and SKU are required.")
                        else:
                            image_path_to_save = current_image_path # Keep old if no new one
                            if new_uploaded_image:
                                # Save new image, potentially remove old one
                                image_path_to_save = save_uploaded_file(new_uploaded_image, prod_id_to_edit)
                                if image_path_to_save is None: # Error in saving
                                    st.error("Could not save new image.")
                                    # Potentially revert to old image path or handle error
                            try:
                                db.update_product(prod_id_to_edit, name, sku, desc, category, material, dims, cost, sell, qty, reorder, supplier_id, image_path_to_save)
                                st.success("Product updated successfully!")
                                st.experimental_rerun()
                            except sqlite3.IntegrityError:
                                st.error(f"SKU '{sku}' already exists for another product.")
                            except Exception as e:
                                st.error(f"An error occurred: {e}")
            else:
                st.error("Product not found.")

    elif action_prod == "Delete Product":
        st.subheader("Delete Product")
        products_list = db.get_all_products()
        product_options = {f"{p['ProductName']} (SKU: {p['SKU']}, ID: {p['ProductID']})": p['ProductID'] for p in products_list}
        selected_prod_display_del = st.selectbox("Select Product to Delete", list(product_options.keys()), key="del_prod_select")

        if selected_prod_display_del:
            prod_id_to_delete = product_options[selected_prod_display_del]
            st.warning(f"Are you sure you want to delete {selected_prod_display_del}? This will also delete its image. This action cannot be undone.")
            if st.button("Confirm Delete Product"):
                try:
                    # Check for related order items before deleting
                    # items_for_product = db.get_order_items_by_product_id(prod_id_to_delete)
                    # if items_for_product:
                    #    st.error("Cannot delete product. It is part of existing orders.")
                    # else:
                    db.delete_product(prod_id_to_delete)
                    st.success("Product deleted successfully!")
                    st.experimental_rerun()
                except Exception as e:
                     st.error(f"Could not delete product. It might be part of existing orders. Error: {e}")


elif choice == "Sales Book (Orders)":
    st.header("🛒 Sales Book (Orders)")
    # This section requires significant rework to integrate with the DB for adding/viewing orders and items.
    # For brevity, I'm showing a simplified "View Orders" and a placeholder for "Add Order".

    st.subheader("Existing Orders")
    all_db_orders = db.get_all_orders()
    if all_db_orders:
        st.dataframe(db.rows_to_dicts(all_db_orders), use_container_width=True)
        
        selected_order_id_view = st.selectbox("Select Order ID to view items", [o['OrderID'] for o in all_db_orders], key="view_order_items_select_db")
        if selected_order_id_view:
            items_for_order = db.get_order_items_by_order_id(selected_order_id_view)
            if items_for_order:
                st.write(f"Items for Order ID: {selected_order_id_view}")
                st.dataframe(db.rows_to_dicts(items_for_order), use_container_width=True)
            else:
                st.info("No items found for this order.")
    else:
        st.info("No orders recorded yet.")

    st.subheader("Add New Order (Simplified)")
    with st.form("add_order_form_db", clear_on_submit=True):
        customers_for_order = db.get_all_customers()
        customer_map = {f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_order}
        selected_cust_name_order = st.selectbox("Customer*", list(customer_map.keys()), key="order_cust_db")
        
        order_date_db = st.date_input("Order Date", datetime.now())
        order_status_db = st.selectbox("Order Status", ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"])
        payment_status_db = st.selectbox("Payment Status", ["Unpaid", "Partially Paid", "Paid"])
        shipping_address_db = st.text_area("Shipping Address") # Auto-fill from customer later
        notes_db = st.text_area("Order Notes")

        # --- Order Items (Very Simplified for this demo) ---
        st.write("**Add Items (Manual Total for Demo)**")
        products_for_items = db.get_all_products()
        # In a real app, you'd have a dynamic way to add multiple items, calculate totals, etc.
        # This is a MAJOR simplification.
        if products_for_items:
            selected_prod_item1 = st.selectbox("Product 1 (Select one for demo)", [f"{p['ProductName']} (ID: {p['ProductID']})" for p in products_for_items], key="item1_prod_db")
            qty_item1 = st.number_input("Quantity Product 1", min_value=1, value=1, step=1, key="item1_qty_db")
        
        total_amount_manual = st.number_input("Manually Enter Total Order Amount ($)", min_value=0.0, format="%.2f", help="Auto-calculate this in a full version")

        submitted_order_db = st.form_submit_button("Create Order")

        if submitted_order_db:
            if not selected_cust_name_order or total_amount_manual <= 0:
                st.error("Customer and Total Amount are required.")
            else:
                customer_id_for_order = customer_map[selected_cust_name_order]
                
                # Add the main order
                new_order_id = db.add_order(
                    order_date_db.strftime("%Y-%m-%d"), 
                    customer_id_for_order, 
                    order_status_db, 
                    total_amount_manual,
                    payment_status_db,
                    shipping_address_db,
                    notes_db
                )
                st.success(f"Order (ID: {new_order_id}) created with manual total.")

                # Add the demo item (if selected)
                if products_for_items and selected_prod_item1:
                    prod_id_item1 = int(selected_prod_item1.split(" (ID: ")[1][:-1]) # Extract ID
                    product_details_item1 = db.get_product_by_id(prod_id_item1)
                    if product_details_item1:
                        unit_price_item1 = product_details_item1['SellingPrice']
                        line_total_item1 = qty_item1 * unit_price_item1
                        db.add_order_item(new_order_id, prod_id_item1, qty_item1, unit_price_item1, 0, line_total_item1)
                        # Update stock
                        db.update_product_stock(prod_id_item1, -qty_item1) # Deduct stock
                        st.info(f"Item '{product_details_item1['ProductName']}' added to order and stock updated.")
                
                # Add to Cash Flow and Tax (simplified, as before)
                # ...
                st.experimental_rerun()


elif choice == "Expense Tracking":
    st.header("💸 Expense Tracking")
    action_exp = st.selectbox("Action", ["View All", "Add New"], key="exp_action")

    if action_exp == "View All":
        st.subheader("Recorded Expenses")
        all_db_expenses = db.get_all_expenses()
        if all_db_expenses:
            st.dataframe(db.rows_to_dicts(all_db_expenses), use_container_width=True)
        else:
            st.info("No expenses recorded yet.")
    
    elif action_exp == "Add New":
        st.subheader("Add New Expense")
        with st.form("add_expense_form_db", clear_on_submit=True):
            exp_date = st.date_input("Expense Date", datetime.now())
            desc_exp = st.text_input("Description*")
            cat_exp_opts = ["Operational", "Marketing", "COGS", "Salaries", "Utilities", "Rent", "Travel", "Other"]
            cat_exp = st.selectbox("Category", cat_exp_opts)
            amt_exp = st.number_input("Amount ($)*", min_value=0.01, format="%.2f")
            vendor_exp = st.text_input("Vendor/Payee")
            # project_id_exp = ... (if project module is implemented)
            receipt_ref_exp = st.text_input("Receipt Reference")
            submitted_exp = st.form_submit_button("Add Expense")

            if submitted_exp:
                if not desc_exp or amt_exp <= 0:
                    st.error("Description and a valid Amount are required.")
                else:
                    db.add_expense(exp_date.strftime("%Y-%m-%d"), desc_exp, cat_exp, amt_exp, vendor_exp, None, receipt_ref_exp)
                    st.success("Expense added successfully!")
                    # Add to cash flow if needed (outflow)
                    # ...

elif choice == "Reports":
    st.header("📈 Reports")
    st.info("Reporting section needs to be updated to query data from the SQLite database. This is a placeholder.")
    # Example: P/L
    # total_revenue = sum(o['TotalAmount'] for o in db.get_all_orders() if o['TotalAmount'])
    # total_expenses = sum(e['Amount'] for e in db.get_all_expenses() if e['Amount'])
    # st.metric("Total Revenue (from DB)", f"${total_revenue:,.2f}")
    # st.metric("Total Expenses (from DB)", f"${total_expenses:,.2f}")
    # ... more complex COGS calculation needed ...


st.sidebar.markdown("---")
st.sidebar.info("Management System v0.3")
