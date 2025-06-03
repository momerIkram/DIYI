import streamlit as st
import pandas as pd
from datetime import datetime
import os
import database as db # Your database module
from PIL import Image

st.set_page_config(layout="wide")
st.title("🛋️ DYI Furniture Management System (v0.4 - Expanded Schema)")

# --- Helper for saving uploaded file ---
def save_uploaded_file(uploaded_file, object_type, object_id):
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        filename = f"{object_type}_{object_id}{file_extension}"
        img_path = os.path.join(db.IMAGE_DIR, filename)
        
        # Simplified: Overwrite if exists for this specific ID.
        # More complex logic might be needed for old image removal if filename changes
        with open(img_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return img_path
    return None

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
modules = [
    "Dashboard", "Customer Management", "Supplier Management",
    "Material Management", "Product Management", "Project Management",
    "Sales Book (Orders)", "Expense Tracking", "Reports"
]
choice = st.sidebar.radio("Go to", modules)

# --- Module Implementations ---

if choice == "Dashboard":
    st.header("📊 Dashboard")
    # ... (Dashboard logic remains similar, querying new tables if needed) ...
    customers = db.get_all_customers()
    products = db.get_all_products()
    suppliers = db.get_all_suppliers()
    materials = db.get_all_materials()
    projects = db.get_all_projects()
    orders = db.get_all_orders()
    expenses = db.get_all_expenses()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Customers", len(customers))
    col2.metric("Total Products", len(products))
    col3.metric("Total Suppliers", len(suppliers))
    col4.metric("Total Materials", len(materials))
    
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Total Projects", len(projects))
    
    total_revenue = sum(o['TotalAmount'] for o in orders if o['TotalAmount']) if orders else 0
    col6.metric("Total Sales Revenue", f"${total_revenue:,.2f}")
    
    total_expenses = sum(e['Amount'] for e in expenses if e['Amount']) if expenses else 0
    col7.metric("Total Expenses", f"${total_expenses:,.2f}")
    
    st.subheader("Recent Orders")
    if orders:
        st.dataframe(db.rows_to_dicts(orders[:5]), use_container_width=True)
    else:
        st.info("No orders yet.")


elif choice == "Customer Management":
    st.header("👥 Customer Management")
    # ... (Customer UI logic largely remains similar - uses existing db functions) ...
    # Ensure forms match the fields defined in the table if any discrepancy.
    action = st.selectbox("Action", ["View All", "Add New", "Edit Customer", "Delete Customer"], key="cust_action_key")

    if action == "View All":
        st.subheader("Existing Customers")
        search_term_cust = st.text_input("Search Customers (by Name or Email)", key="search_cust_view")
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
                if not name: st.error("Customer Name is required.")
                else:
                    try:
                        db.add_customer(name, email, phone, bill_addr, ship_addr or bill_addr, notes)
                        st.success("Customer added successfully!")
                    except Exception as e: st.error(f"Error: {e}")
    
    # Edit and Delete for Customer Management needs to be implemented with db calls like in Product Management example

elif choice == "Supplier Management":
    st.header("🚚 Supplier Management")
    action_sup = st.selectbox("Action", ["View All", "Add New", "Edit Supplier", "Delete Supplier"], key="sup_action")

    if action_sup == "View All":
        st.subheader("Existing Suppliers")
        search_term_sup = st.text_input("Search Suppliers (Name, Contact, Email)", key="search_sup_view")
        suppliers_list = db.get_all_suppliers(search_term=search_term_sup)
        if suppliers_list:
            st.dataframe(db.rows_to_dicts(suppliers_list), use_container_width=True)
        else:
            st.info("No suppliers found.")

    elif action_sup == "Add New":
        st.subheader("Add New Supplier")
        with st.form("add_supplier_form", clear_on_submit=True):
            s_name = st.text_input("Supplier Name*")
            s_contact = st.text_input("Contact Person")
            s_email = st.text_input("Email")
            s_phone = st.text_input("Phone")
            s_address = st.text_area("Address")
            submitted = st.form_submit_button("Add Supplier")
            if submitted:
                if not s_name: st.error("Supplier Name is required.")
                else:
                    try:
                        db.add_supplier(s_name, s_contact, s_email, s_phone, s_address)
                        st.success("Supplier added!")
                    except Exception as e: st.error(f"Error: {e}")
    
    elif action_sup == "Edit Supplier":
        st.subheader("Edit Supplier")
        suppliers_list_edit = db.get_all_suppliers()
        if not suppliers_list_edit:
            st.info("No suppliers to edit.")
        else:
            supplier_options = {f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_list_edit}
            selected_sup_disp = st.selectbox("Select Supplier", list(supplier_options.keys()), key="edit_sup_select")
            if selected_sup_disp:
                sup_id_to_edit = supplier_options[selected_sup_disp]
                sup_data = db.get_supplier_by_id(sup_id_to_edit)
                if sup_data:
                    with st.form(f"edit_supplier_form_{sup_id_to_edit}"):
                        st.write(f"Editing Supplier ID: {sup_data['SupplierID']}")
                        s_name = st.text_input("Supplier Name*", value=sup_data['SupplierName'])
                        s_contact = st.text_input("Contact Person", value=sup_data['ContactPerson'])
                        s_email = st.text_input("Email", value=sup_data['Email'])
                        s_phone = st.text_input("Phone", value=sup_data['Phone'])
                        s_address = st.text_area("Address", value=sup_data['Address'])
                        updated = st.form_submit_button("Update Supplier")
                        if updated:
                            if not s_name: st.error("Supplier Name is required.")
                            else:
                                try:
                                    db.update_supplier(sup_id_to_edit, s_name, s_contact, s_email, s_phone, s_address)
                                    st.success("Supplier updated!")
                                    st.experimental_rerun()
                                except Exception as e: st.error(f"Error: {e}")
    
    elif action_sup == "Delete Supplier":
        st.subheader("Delete Supplier")
        # Similar logic to delete customer/product using db.delete_supplier
        # Make sure to handle potential errors if supplier is linked.

elif choice == "Material Management":
    st.header("🧱 Material Management")
    action_mat = st.selectbox("Action", ["View All", "Add New", "Edit Material", "Delete Material"], key="mat_action")

    # --- Supplier Dropdown for Material Form ---
    suppliers_for_mat = db.get_all_suppliers()
    supplier_map_mat = {"None (No Supplier)": None} # Option for no supplier
    supplier_map_mat.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_for_mat})

    if action_mat == "View All":
        st.subheader("Existing Materials")
        search_term_mat = st.text_input("Search Materials (Name, Type, Supplier)", key="search_mat_view")
        materials_list = db.get_all_materials(search_term=search_term_mat)
        if materials_list:
            st.dataframe(db.rows_to_dicts(materials_list), use_container_width=True)
        else: st.info("No materials found.")

    elif action_mat == "Add New":
        st.subheader("Add New Material")
        with st.form("add_material_form", clear_on_submit=True):
            m_name = st.text_input("Material Name*")
            m_type = st.text_input("Material Type (e.g., Wood, Fabric)")
            m_unit = st.text_input("Unit of Measure (e.g., m, kg, piece)")
            m_cost_unit = st.number_input("Cost Per Unit ($)", min_value=0.0, format="%.2f")
            m_qty = st.number_input("Quantity In Stock", format="%.2f") # Allow float
            selected_sup_name_mat = st.selectbox("Supplier", list(supplier_map_mat.keys()), key="add_mat_supplier")
            m_supplier_id = supplier_map_mat[selected_sup_name_mat]
            submitted = st.form_submit_button("Add Material")
            if submitted:
                if not m_name: st.error("Material Name required.")
                else:
                    try:
                        db.add_material(m_name, m_type, m_unit, m_cost_unit, m_qty, m_supplier_id)
                        st.success("Material added!")
                    except Exception as e: st.error(f"Error: {e}")
    # Edit and Delete for Material Management to be implemented.

elif choice == "Product Management":
    st.header("📦 Product Management (Inventory)")
    action_prod = st.selectbox("Action", ["View All", "Add New", "Edit Product", "Delete Product"], key="prod_action_key")

    # --- Supplier Dropdown for Product Form ---
    suppliers_for_prod = db.get_all_suppliers()
    supplier_map_prod = {"None (No Supplier)": None}
    supplier_map_prod.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_for_prod})


    if action_prod == "View All":
        st.subheader("Existing Products")
        # ... (View All products logic from previous version, ensure it shows SupplierName from join) ...
        search_term_prod = st.text_input("Search Products (Name, SKU, Category, Supplier)", key="search_prod_view")
        products_list = db.get_all_products(search_term=search_term_prod)
        if products_list:
            df_products = pd.DataFrame(db.rows_to_dicts(products_list))
            cols_to_display = [col for col in df_products.columns if col not in ['ImagePath','SupplierID']] # Display SupplierName instead of ID
            if 'SupplierID' in cols_to_display and 'SupplierName' in df_products.columns : # just in case join failed
                cols_to_display.remove('SupplierID')

            st.dataframe(df_products[cols_to_display], use_container_width=True)
            for prod_row_dict in db.rows_to_dicts(products_list): # Iterate over list of dicts
                if prod_row_dict.get('ImagePath') and os.path.exists(prod_row_dict['ImagePath']):
                    with st.expander(f"{prod_row_dict['ProductName']} - Image"):
                        try:
                            image = Image.open(prod_row_dict['ImagePath'])
                            st.image(image, caption=prod_row_dict['ProductName'], width=200)
                        except Exception as e: st.warning(f"Could not load image: {e}")
        else: st.info("No products found.")


    elif action_prod == "Add New":
        st.subheader("Add New Product")
        with st.form("add_product_form", clear_on_submit=True):
            p_name = st.text_input("Product Name*")
            p_sku = st.text_input("SKU (Unique)")
            p_desc = st.text_area("Description")
            p_cat = st.text_input("Category (e.g., Sofa, Table)")
            p_mat_type = st.text_input("Material Type (e.g., Wood, Fabric)") # Main material
            p_dims = st.text_input("Dimensions (L x W x H)")
            p_cost = st.number_input("Cost Price ($)", min_value=0.0, format="%.2f")
            p_sell = st.number_input("Selling Price ($)", min_value=0.0, format="%.2f")
            p_qty = st.number_input("Quantity In Stock", min_value=0, step=1)
            p_reorder = st.number_input("Reorder Level", min_value=0, step=1)
            
            selected_sup_name_prod = st.selectbox("Supplier", list(supplier_map_prod.keys()), key="add_prod_supplier")
            p_supplier_id = supplier_map_prod[selected_sup_name_prod]
            
            p_uploaded_image = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"])
            
            submitted = st.form_submit_button("Add Product")
            if submitted:
                if not p_name or not p_sku: st.error("Product Name and SKU required.")
                else:
                    p_image_path = None
                    # Save image after product insert to use ProductID in filename
                    try:
                        # Temporarily add product without image to get ID or add with temp name
                        # This is tricky: ideally, insert, get ID, save image, update product record.
                        # For simplicity now, save image with SKU (if it must be unique for image name)
                        if p_uploaded_image:
                            # Create a somewhat unique name before ID is known
                             p_image_path = save_uploaded_file(p_uploaded_image, "temp_product", p_sku)


                        db.add_product(p_name, p_sku, p_desc, p_cat, p_mat_type, p_dims, p_cost, p_sell, p_qty, p_reorder, p_supplier_id, p_image_path)
                        st.success("Product added!")
                        # If using temp_product name for image, find product and rename image file with ProductID & update DB record.

                    except Exception as e: st.error(f"Error: {e}")
    # Edit and Delete for Product Management to be implemented, ensuring all fields and image handling are covered.


elif choice == "Project Management":
    st.header("🛠️ Project Management")
    action_proj = st.selectbox("Action", ["View All", "Add New", "Edit Project", "Delete Project"], key="proj_action")

    # --- Customer Dropdown for Project Form ---
    customers_for_proj = db.get_all_customers()
    customer_map_proj = {"None": None}
    customer_map_proj.update({f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_proj})
    
    project_status_options = ["Planning", "In Progress", "On Hold", "Completed", "Cancelled"]


    if action_proj == "View All":
        st.subheader("Existing Projects")
        search_term_proj = st.text_input("Search Projects (Name, Customer, Status)", key="search_proj_view")
        projects_list = db.get_all_projects(search_term=search_term_proj)
        if projects_list:
            st.dataframe(db.rows_to_dicts(projects_list), use_container_width=True)
        else: st.info("No projects found.")

    elif action_proj == "Add New":
        st.subheader("Add New Project")
        with st.form("add_project_form", clear_on_submit=True):
            pr_name = st.text_input("Project Name*")
            selected_cust_name_proj = st.selectbox("Customer", list(customer_map_proj.keys()), key="add_proj_customer")
            pr_customer_id = customer_map_proj[selected_cust_name_proj]
            
            col_start, col_end = st.columns(2)
            pr_start_date = col_start.date_input("Start Date", datetime.now().date())
            pr_end_date = col_end.date_input("Expected End Date", (datetime.now() + pd.Timedelta(days=30)).date() )
            
            pr_status = st.selectbox("Status", project_status_options)
            pr_budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f")
            pr_desc = st.text_area("Description")
            
            submitted = st.form_submit_button("Add Project")
            if submitted:
                if not pr_name: st.error("Project Name required.")
                else:
                    try:
                        db.add_project(pr_name, pr_customer_id, 
                                       pr_start_date.strftime("%Y-%m-%d") if pr_start_date else None, 
                                       pr_end_date.strftime("%Y-%m-%d") if pr_end_date else None, 
                                       pr_status, pr_budget, pr_desc)
                        st.success("Project added!")
                    except Exception as e: st.error(f"Error: {e}")
    # Edit and Delete for Project Management to be implemented.

elif choice == "Sales Book (Orders)":
    st.header("🛒 Sales Book (Orders)")
    st.info("Order items management (adding/editing specific items within an order form) is complex and requires more advanced Streamlit techniques (like session state for dynamic rows). The 'Add Order' form below is simplified.")

    action_order = st.selectbox("Action", ["View All Orders", "Create New Order"], key="order_action")

    if action_order == "View All Orders":
        st.subheader("Existing Orders")
        all_db_orders = db.get_all_orders()
        if all_db_orders:
            st.dataframe(db.rows_to_dicts(all_db_orders), use_container_width=True)
            order_ids_for_view = [o['OrderID'] for o in all_db_orders]
            if order_ids_for_view:
                selected_order_id_view = st.selectbox("Select Order ID to view items", order_ids_for_view, key="view_order_items_select_db")
                if selected_order_id_view:
                    items_for_order = db.get_order_items_by_order_id(selected_order_id_view)
                    if items_for_order:
                        st.write(f"Items for Order ID: {selected_order_id_view}")
                        st.dataframe(db.rows_to_dicts(items_for_order), use_container_width=True)
                    else: st.info("No items found for this order.")
        else: st.info("No orders recorded yet.")

    elif action_order == "Create New Order":
        st.subheader("Create New Order")
        
        customers_for_order = db.get_all_customers()
        customer_map_order = {"None": None}
        customer_map_order.update({f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_order})
        
        projects_for_order = db.get_all_projects()
        project_map_order = {"None (No Project)": None}
        project_map_order.update({f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_for_order})

        order_status_options = ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
        payment_status_options = ["Unpaid", "Partially Paid", "Paid", "Refunded"]

        with st.form("add_order_form_db", clear_on_submit=False): # clear_on_submit = False for multi-stage
            o_order_date = st.date_input("Order Date", datetime.now().date())
            selected_cust_name_order = st.selectbox("Customer*", list(customer_map_order.keys()), key="order_cust_db_select")
            o_customer_id = customer_map_order.get(selected_cust_name_order)
            
            selected_proj_name_order = st.selectbox("Associated Project (Optional)", list(project_map_order.keys()), key="order_proj_db_select")
            o_project_id = project_map_order.get(selected_proj_name_order)

            col_ord_stat1, col_ord_stat2 = st.columns(2)
            o_order_status = col_ord_stat1.selectbox("Order Status", order_status_options)
            o_payment_status = col_ord_stat2.selectbox("Payment Status", payment_status_options)
            
            o_shipping_address = st.text_area("Shipping Address (Auto-fills from customer if blank and customer selected)")
            o_notes = st.text_area("Order Notes")

            st.markdown("---")
            st.subheader("Order Items")
            if 'current_order_items' not in st.session_state:
                st.session_state.current_order_items = []

            products_for_items_order = db.get_all_products()
            product_map_order_items = {"Select Product": None}
            product_map_order_items.update({f"{p['ProductName']} (ID: {p['ProductID']}, Price: ${p['SellingPrice']:.2f}, Stock: {p['QuantityInStock']})": p['ProductID'] for p in products_for_items_order})

            item_cols = st.columns([3, 1, 1, 1, 0.5])
            selected_prod_disp_item = item_cols[0].selectbox("Product", list(product_map_order_items.keys()), key="order_item_prod_select")
            qty_item = item_cols[1].number_input("Qty", min_value=1, value=1, step=1, key="order_item_qty_val")
            
            prod_id_for_price = product_map_order_items.get(selected_prod_disp_item)
            default_unit_price = 0.0
            if prod_id_for_price:
                prod_details = db.get_product_by_id(prod_id_for_price)
                if prod_details: default_unit_price = float(prod_details['SellingPrice'])

            unit_price_item_override = item_cols[2].number_input("Unit Price", min_value=0.0, value=default_unit_price, format="%.2f", key="order_item_price_val")
            discount_item_val = item_cols[3].number_input("Discount ($)", min_value=0.0, value=0.0, format="%.2f", key="order_item_disc_val")

            if item_cols[4].button("➕ Add", key="order_add_item_button"):
                if prod_id_for_price and qty_item > 0:
                    prod_details = db.get_product_by_id(prod_id_for_price) # Re-fetch for name
                    if prod_details['QuantityInStock'] < qty_item:
                        st.warning(f"Not enough stock for {prod_details['ProductName']} (Available: {prod_details['QuantityInStock']}).")
                    else:
                        st.session_state.current_order_items.append({
                            'ProductID': prod_id_for_price,
                            'ProductName': prod_details['ProductName'], # For display in temp table
                            'QuantitySold': qty_item,
                            'UnitPriceAtSale': unit_price_item_override,
                            'Discount': discount_item_val,
                            'LineTotal': (unit_price_item_override * qty_item) - discount_item_val
                        })
                        st.experimental_rerun() # To update display of items
                else: st.warning("Please select a product and quantity.")

            if st.session_state.current_order_items:
                st.markdown("**Items in this Order:**")
                temp_items_df = pd.DataFrame(st.session_state.current_order_items)
                st.dataframe(temp_items_df[['ProductName', 'QuantitySold', 'UnitPriceAtSale', 'Discount', 'LineTotal']], use_container_width=True)
                current_total_amount = temp_items_df['LineTotal'].sum()
                st.metric("Calculated Order Total", f"${current_total_amount:,.2f}")
            else:
                current_total_amount = 0.0
            
            # Auto-fill shipping address
            if not o_shipping_address and o_customer_id:
                cust_details_for_addr = db.get_customer_by_id(o_customer_id)
                if cust_details_for_addr and cust_details_for_addr['ShippingAddress']:
                    o_shipping_address = cust_details_for_addr['ShippingAddress']
                    st.text_area("Shipping Address (Auto-fills...)", value=o_shipping_address, key="order_ship_addr_filled", disabled=True) # Show auto-filled
                elif cust_details_for_addr and cust_details_for_addr['BillingAddress']: # fallback to billing
                     o_shipping_address = cust_details_for_addr['BillingAddress']
                     st.text_area("Shipping Address (Auto-fills...)", value=o_shipping_address, key="order_ship_addr_filled_bill", disabled=True)

            submitted_order_db = st.form_submit_button("💾 Create Order")
            if submitted_order_db:
                if not o_customer_id: st.error("Customer is required.")
                elif not st.session_state.current_order_items: st.error("Order must have at least one item.")
                else:
                    try:
                        final_shipping_address = o_shipping_address # Use what's in the live text_area if edited
                        
                        new_order_id = db.add_order(
                            o_order_date.strftime("%Y-%m-%d"), o_customer_id, o_project_id,
                            o_order_status, 0, # Initial total 0, will update after adding items
                            o_payment_status, final_shipping_address, o_notes
                        )
                        # Add order items to DB and update stock
                        for item_data in st.session_state.current_order_items:
                            db.add_order_item(new_order_id, item_data['ProductID'], item_data['QuantitySold'],
                                              item_data['UnitPriceAtSale'], item_data['Discount'])
                            db.update_product_stock(item_data['ProductID'], -item_data['QuantitySold']) # Deduct stock
                        
                        db.update_order_total(new_order_id) # Recalculate and save total based on DB items
                        
                        st.success(f"Order (ID: {new_order_id}) created successfully!")
                        # Add to CashFlow, Tax etc. as needed
                        st.session_state.current_order_items = [] # Clear for next order
                        st.experimental_rerun()
                    except Exception as e: st.error(f"Error creating order: {e}")

elif choice == "Expense Tracking":
    st.header("💸 Expense Tracking")
    # ... (Expense UI needs to be updated to include ProjectID dropdown similar to other modules) ...
    projects_for_exp = db.get_all_projects()
    project_map_exp = {"None (No Project)": None}
    project_map_exp.update({f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_for_exp})

    action_exp = st.selectbox("Action", ["View All", "Add New"], key="exp_action_key")

    if action_exp == "View All":
        st.subheader("Recorded Expenses")
        all_db_expenses = db.get_all_expenses()
        if all_db_expenses:
            st.dataframe(db.rows_to_dicts(all_db_expenses), use_container_width=True)
        else: st.info("No expenses recorded yet.")
    
    elif action_exp == "Add New":
        st.subheader("Add New Expense")
        with st.form("add_expense_form_db", clear_on_submit=True):
            exp_date = st.date_input("Expense Date", datetime.now().date())
            desc_exp = st.text_input("Description*")
            cat_exp_opts = ["Operational", "Marketing", "COGS", "Raw Material Purchase", "Salaries", "Utilities", "Rent", "Travel", "Other"]
            cat_exp = st.selectbox("Category", cat_exp_opts)
            amt_exp = st.number_input("Amount ($)*", min_value=0.01, format="%.2f")
            vendor_exp = st.text_input("Vendor/Payee")
            selected_proj_name_exp = st.selectbox("Associated Project (Optional)", list(project_map_exp.keys()), key="exp_proj_db_select")
            exp_project_id = project_map_exp.get(selected_proj_name_exp)
            receipt_ref_exp = st.text_input("Receipt Reference")
            
            submitted_exp = st.form_submit_button("Add Expense")
            if submitted_exp:
                if not desc_exp or amt_exp <= 0: st.error("Description and a valid Amount are required.")
                else:
                    try:
                        db.add_expense(exp_date.strftime("%Y-%m-%d"), desc_exp, cat_exp, amt_exp, vendor_exp, exp_project_id, receipt_ref_exp)
                        st.success("Expense added successfully!")
                        # Add to cash flow (outflow) if needed
                    except Exception as e: st.error(f"Error: {e}")


elif choice == "Reports":
    st.header("📈 Reports")
    st.info("Reporting section needs to query from the database for generating dynamic reports.")
    # This part would involve more complex queries and possibly using pandas for data manipulation
    # before displaying with Streamlit's charting or table elements.

st.sidebar.markdown("---")
st.sidebar.info("Management System v0.4")
