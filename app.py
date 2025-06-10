

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import database as db # Your database module
from PIL import Image

# --- Initialize Database Schema ---
# Ensure this is called once at the start of your application
try:
    db.init_db()
    # You can add a success message to the sidebar or logs if you want confirmation
    # st.sidebar.info("Database initialized.") # Optional
except Exception as e:
    st.error(f"Fatal Error: Database could not be initialized: {e}")
    st.warning("The application cannot proceed without a valid database connection and schema.")
    st.stop() # Stop the app if DB initialization fails
# ---------------------------------

# --- db.py needs to ensure these tables and columns exist ---
# Example: In db.init_db():
#   add_customer_fields_if_not_exist() # To add ReferenceID to Customers
#   add_order_fields_if_not_exist()    # To add ReferenceID to Orders
#   create_invoices_table()
#   Ensure Projects table has CustomerID
#   create_project_materials_table() # NEW
# --------------------------------------------------------------

st.set_page_config(layout="wide")
st.title("🛋️ DYI Furniture Management System")

# ... (rest of your app.py code) ...

st.set_page_config(layout="wide")
st.title("🛋️ DYI Furniture Management System")

# --- Helper for saving uploaded file (modified for receipts) ---
def save_uploaded_receipt(uploaded_file, service_id): # Changed parameters
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        if not os.path.exists(db.RECEIPT_DIR):
            os.makedirs(db.RECEIPT_DIR)
        filename = f"service_{service_id}_receipt{file_extension}"
        receipt_path = os.path.join(db.RECEIPT_DIR, filename)
        with open(receipt_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return receipt_path
    return None

def save_uploaded_product_image(uploaded_file, product_id_or_sku):
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        if not os.path.exists(db.IMAGE_DIR):
            os.makedirs(db.IMAGE_DIR)
        filename = f"product_{product_id_or_sku}{file_extension}"
        img_path = os.path.join(db.IMAGE_DIR, filename)
        with open(img_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return img_path
    return None

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
modules = [
    "Dashboard", "Customer Management", "Supplier Management",
    "Supplier Services",
    "Material Management", "Product Management", "Project Management",
    "Sales Book (Orders)", "Invoice Tracking", 
    "Expense Tracking", "Reports"
]
choice = st.sidebar.radio("Go to", modules)

# Initialize session state
if 'selected_customer_id_for_detail_view' not in st.session_state:
    st.session_state.selected_customer_id_for_detail_view = None
if 'customer_management_action_view' not in st.session_state:
    st.session_state.customer_management_action_view = "List"
if 'active_selection_for_button_cust_id' not in st.session_state:
    st.session_state.active_selection_for_button_cust_id = None
if 'active_selection_for_button_cust_name' not in st.session_state:
    st.session_state.active_selection_for_button_cust_name = None
if 'current_order_items_main' not in st.session_state: # For Sales Book
    st.session_state.current_order_items_main = []


# --- Module Implementations ---

if choice == "Dashboard":
    st.header("📊 Dashboard")
    customers = db.get_all_customers()
    products = db.get_all_products()
    suppliers = db.get_all_suppliers()
    materials = db.get_all_materials()
    try:
        projects_rows = db.get_all_projects() 
        projects = db.rows_to_dicts(projects_rows) if projects_rows else []
    except Exception as e:
        st.error(f"Error loading project data for Dashboard: {e}")
        st.warning("The Dashboard might be incomplete. This could be due to a database schema issue (e.g., missing 'Projects.CustomerID'). Please check `database.py`.")
        projects = [] 

    expenses_rows = db.get_all_expenses()
    expenses = db.rows_to_dicts(expenses_rows) if expenses_rows else []
    services_rows = db.get_all_supplier_services()
    services_count = len(services_rows) if services_rows else 0
    invoices_rows = db.get_all_invoices() 
    invoices = db.rows_to_dicts(invoices_rows) if invoices_rows else []


    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Customers", len(db.rows_to_dicts(customers)) if customers else 0)
    col2.metric("Total Products", len(db.rows_to_dicts(products)) if products else 0)
    col3.metric("Total Suppliers", len(db.rows_to_dicts(suppliers)) if suppliers else 0)
    col4.metric("Total Materials", len(db.rows_to_dicts(materials)) if materials else 0)

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Total Projects", len(projects) if projects else 0)

    total_revenue_from_invoices = sum(inv['TotalAmount'] for inv in invoices if inv.get('Status') == 'Paid' and inv.get('TotalAmount'))
    col6.metric("Total Sales Revenue (from Paid Invoices)", f"Rs. {total_revenue_from_invoices:,.2f}")

    total_expenses_val = sum(e['Amount'] for e in expenses if e.get('Amount'))
    col7.metric("Total Expenses", f"Rs. {total_expenses_val:,.2f}")
    col8.metric("Total Supplier Services Logged", services_count)

    st.subheader("Recent Orders")
    recent_orders_rows = db.get_all_orders(limit=5) 
    if recent_orders_rows:
        st.dataframe(db.rows_to_dicts(recent_orders_rows), use_container_width=True)
    else:
        st.info("No orders yet.")

    st.subheader("Recent Invoices")
    if invoices:
        recent_invoices_df = pd.DataFrame(invoices) # invoices is already list of dicts
        if not recent_invoices_df.empty:
            recent_invoices_df['IssueDate'] = pd.to_datetime(recent_invoices_df['IssueDate'])
            if 'PaymentDate' in recent_invoices_df.columns:
                recent_invoices_df['PaymentDate_Display'] = pd.to_datetime(recent_invoices_df['PaymentDate'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('N/A')
            else:
                recent_invoices_df['PaymentDate_Display'] = 'N/A'
            
            recent_invoices_df = recent_invoices_df.sort_values(by='IssueDate', ascending=False).head(5)
            
            cols_recent_inv_display = ['InvoiceReferenceID', 'CustomerName', 'ProjectName', 'TotalAmount', 'Status', 'IssueDate']
            if 'PaymentDate_Display' in recent_invoices_df.columns: # Check again on the potentially modified df
                cols_recent_inv_display.append('PaymentDate_Display')
            
            final_cols_recent_inv = [col for col in cols_recent_inv_display if col in recent_invoices_df.columns]
            st.dataframe(recent_invoices_df[final_cols_recent_inv], use_container_width=True, hide_index=True)
        else:
            st.info("No invoices yet.")
    else:
        st.info("No invoices yet.")


elif choice == "Customer Management":
    st.header("👥 Customer Management")

    if 'customer_management_action_view' not in st.session_state:
        st.session_state.customer_management_action_view = "List"

    if st.session_state.customer_management_action_view == "List":
        action = st.selectbox("Action", ["View All Customers", "Add New", "Edit Customer", "Delete Customer"], key="cust_action_selector")

        if action == "View All Customers":
            st.subheader("Existing Customers")
            search_term_cust = st.text_input("Search Customers (by Name, Email, or Ref ID)", key="search_cust_view_all")
            customers_list_rows = db.get_all_customers(search_term=search_term_cust)
            
            if customers_list_rows:
                customers_dicts = db.rows_to_dicts(customers_list_rows)
                if not customers_dicts:
                    st.info("No customers found or added yet.")
                else:
                    df_customers = pd.DataFrame(customers_dicts)
                    cols_to_show = ['CustomerID', 'CustomerName', 'Email', 'Phone', 'ReferenceID', 'BillingAddress', 'ShippingAddress', 'Notes']
                    cols_to_show_filtered = [col for col in cols_to_show if col in df_customers.columns]
                    
                    st.dataframe(df_customers[cols_to_show_filtered],
                                 use_container_width=True,
                                 key="customer_df_main_list", 
                                 on_select="rerun",
                                 selection_mode="single-row",
                                 hide_index=True)

                    dataframe_selection_state = st.session_state.get("customer_df_main_list", None)
                    
                    if dataframe_selection_state and dataframe_selection_state.selection.rows:
                        selected_row_index = dataframe_selection_state.selection.rows[0]
                        if not df_customers.empty and selected_row_index < len(df_customers):
                            st.session_state.active_selection_for_button_cust_id = df_customers.iloc[selected_row_index]['CustomerID']
                            st.session_state.active_selection_for_button_cust_name = df_customers.iloc[selected_row_index]['CustomerName']
                        else:
                            st.session_state.active_selection_for_button_cust_id = None
                            st.session_state.active_selection_for_button_cust_name = None
                    else: # This else might be hit on initial load or after deselection logic.
                        # If a button was just clicked, this part should ideally not clear the state needed for the button press itself.
                        # The current logic for on_select="rerun" and then button click should be okay if session state for button is stable.
                        # To be safe, only clear if it's explicitly a de-selection event or df is empty.
                        # For now, this simpler logic is kept; if issues, more nuanced handling of dataframe_selection_state needed.
                        if not (dataframe_selection_state and dataframe_selection_state.selection.rows):
                             st.session_state.active_selection_for_button_cust_id = None
                             st.session_state.active_selection_for_button_cust_name = None


                    if st.session_state.active_selection_for_button_cust_id is not None:
                        cust_id_for_btn = st.session_state.active_selection_for_button_cust_id
                        cust_name_for_btn = str(st.session_state.active_selection_for_button_cust_name) if st.session_state.active_selection_for_button_cust_name is not None else "N/A"
                        
                        if st.button(f"View Details for {cust_name_for_btn} (ID: {cust_id_for_btn})", key=f"view_detail_btn_for_{cust_id_for_btn}"):
                            st.session_state.selected_customer_id_for_detail_view = cust_id_for_btn
                            st.session_state.customer_management_action_view = "Details"
                            st.session_state.active_selection_for_button_cust_id = None 
                            st.session_state.active_selection_for_button_cust_name = None
                            st.rerun()
            else:
                st.info("No customers found or added yet.")
        # ... (Rest of Customer Management Add, Edit, Delete as before) ...
        elif action == "Add New":
            st.subheader("Add New Customer")
            with st.form("add_customer_form", clear_on_submit=True):
                name = st.text_input("Customer Name*")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                reference_id = st.text_input("Reference ID (Optional, e.g., CUST-001)")
                bill_addr = st.text_area("Billing Address")
                ship_addr = st.text_area("Shipping Address (if different)")
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("Add Customer")
                if submitted:
                    if not name: st.error("Customer Name is required.")
                    else:
                        try:
                            db.add_customer(name, email, phone, reference_id, bill_addr, ship_addr or bill_addr, notes)
                            st.success("Customer added successfully!")
                        except Exception as e: st.error(f"Error: {e}")
        
        elif action == "Edit Customer":
            st.subheader("Edit Customer")
            customers_list_edit_rows = db.get_all_customers()
            if not customers_list_edit_rows: 
                st.info("No customers to edit.")
            else:
                customers_list_edit = db.rows_to_dicts(customers_list_edit_rows)
                customer_options_edit = {f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_list_edit}
                selected_cust_disp_edit = st.selectbox("Select Customer to Edit", list(customer_options_edit.keys()), key="edit_cust_select_list_view", index=None, placeholder="Select a customer...")
                if selected_cust_disp_edit:
                    cust_id_to_edit = customer_options_edit[selected_cust_disp_edit]
                    cust_data_edit_row = db.get_customer_by_id(cust_id_to_edit) # Expects single row
                    
                    if cust_data_edit_row:
                        cust_data_edit = dict(cust_data_edit_row)

                        if cust_data_edit:
                            with st.form(f"edit_customer_form_list_view_{cust_id_to_edit}"):
                                name = st.text_input("Customer Name*", value=cust_data_edit.get('CustomerName',''))
                                email = st.text_input("Email", value=cust_data_edit.get('Email',''))
                                phone = st.text_input("Phone", value=cust_data_edit.get('Phone',''))
                                st.text_input("Reference ID (Current)", value=cust_data_edit.get('ReferenceID', 'N/A'), disabled=True)
                                new_reference_id = st.text_input("Update Reference ID (Optional)", value=cust_data_edit.get('ReferenceID', ''))
                                bill_addr = st.text_area("Billing Address", value=cust_data_edit.get('BillingAddress',''))
                                ship_addr = st.text_area("Shipping Address", value=cust_data_edit.get('ShippingAddress',''))
                                notes = st.text_area("Notes", value=cust_data_edit.get('Notes',''))
                                updated = st.form_submit_button("Update Customer")
                                if updated:
                                    if not name: st.error("Customer name is required.")
                                    else:
                                        try:
                                            db.update_customer(cust_id_to_edit, name, email, phone, new_reference_id, bill_addr, ship_addr, notes)
                                            st.success("Customer updated successfully!")
                                            st.rerun()
                                        except Exception as e: st.error(f"Error: {e}")
                        else:
                            st.error("Failed to load customer data for editing.")
                    else:
                        st.error(f"Could not find customer with ID {cust_id_to_edit} to edit.")


        elif action == "Delete Customer":
            st.subheader("Delete Customer")
            customers_list_del_rows = db.get_all_customers()
            if not customers_list_del_rows: 
                st.info("No customers to delete.")
            else:
                customers_list_del = db.rows_to_dicts(customers_list_del_rows)
                customer_options_del = {f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_list_del}
                selected_cust_disp_del = st.selectbox("Select Customer to Delete", list(customer_options_del.keys()), key="del_cust_select_list_view", index=None, placeholder="Select a customer...")
                if selected_cust_disp_del:
                    cust_id_to_del = customer_options_del[selected_cust_disp_del]
                    st.warning(f"Are you sure you want to delete {selected_cust_disp_del}? This might fail if the customer has associated records (orders, projects, invoices).")
                    if st.button("Confirm Delete", key=f"confirm_del_cust_list_view_{cust_id_to_del}"):
                        try:
                            db.delete_customer(cust_id_to_del)
                            st.success(f"Customer {selected_cust_disp_del} deleted successfully!")
                            st.session_state.selected_customer_id_for_detail_view = None 
                            st.session_state.active_selection_for_button_cust_id = None 
                            st.session_state.active_selection_for_button_cust_name = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting customer: {e}")

    elif st.session_state.customer_management_action_view == "Details":
        # ... (Customer Details View as previously corrected) ...
        if st.button("⬅️ Back to Customer List"):
            st.session_state.customer_management_action_view = "List"
            st.session_state.selected_customer_id_for_detail_view = None
            st.rerun()

        st.subheader("View Customer Details")
        if st.session_state.selected_customer_id_for_detail_view:
            cust_id = st.session_state.selected_customer_id_for_detail_view
            customer_data_row = db.get_customer_by_id(cust_id) 

            if customer_data_row:
                customer_data = dict(customer_data_row)

                if customer_data:
                    st.markdown(f"### Profile: {customer_data.get('CustomerName', 'N/A')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Reference ID", customer_data.get('ReferenceID', 'N/A'), disabled=True, key=f"detail_ref_{cust_id}")
                        st.text_input("Email", customer_data.get('Email', 'N/A'), disabled=True, key=f"detail_email_{cust_id}")
                        st.text_input("Phone", customer_data.get('Phone', 'N/A'), disabled=True, key=f"detail_phone_{cust_id}")
                    with col2:
                        st.text_area("Billing Address", customer_data.get('BillingAddress', 'N/A'), disabled=True, height=100, key=f"detail_bill_{cust_id}")
                        st.text_area("Shipping Address", customer_data.get('ShippingAddress', 'N/A'), disabled=True, height=100, key=f"detail_ship_{cust_id}")
                    st.text_area("Notes", customer_data.get('Notes', 'N/A'), disabled=True, height=100, key=f"detail_notes_{cust_id}")

                    st.markdown("---")
                    st.markdown("### Order History")
                    customer_orders_rows = db.get_orders_by_customer_id(cust_id)
                    customer_orders = db.rows_to_dicts(customer_orders_rows) if customer_orders_rows else []
                    if customer_orders:
                        orders_df = pd.DataFrame(customer_orders)
                        orders_df['TotalAmount_Display'] = orders_df['TotalAmount'].apply(lambda x: f"Rs. {x:,.2f}" if pd.notnull(x) else "Rs. 0.00")
                        cols_orders = ['OrderID', 'OrderDate', 'ProjectName', 'ReferenceID', 'OrderStatus', 'TotalAmount_Display', 'PaymentStatus']
                        cols_orders_filtered = [col for col in cols_orders if col in orders_df.columns]
                        st.dataframe(orders_df[cols_orders_filtered], use_container_width=True, hide_index=True)
                    else:
                        st.info("No orders found for this customer.")

                    st.markdown("---")
                    st.markdown("### Invoice History")
                    customer_invoices_rows = db.get_invoices_by_customer_id(cust_id)
                    customer_invoices = db.rows_to_dicts(customer_invoices_rows) if customer_invoices_rows else []
                    total_invoiced_amount = 0
                    if customer_invoices:
                        invoices_df = pd.DataFrame(customer_invoices)
                        invoices_df['TotalAmount_Display'] = invoices_df['TotalAmount'].apply(lambda x: f"Rs. {x:,.2f}" if pd.notnull(x) else "Rs. 0.00")
                        invoices_df['IssueDate_Display'] = pd.to_datetime(invoices_df['IssueDate'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('N/A')
                        
                        if 'PaymentDate' in invoices_df.columns:
                            invoices_df['PaymentDate_Display'] = pd.to_datetime(invoices_df['PaymentDate'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('N/A')
                        else:
                            invoices_df['PaymentDate_Display'] = 'N/A'
                        
                        cols_invoices = ['InvoiceReferenceID', 'ProjectName', 'TotalAmount_Display', 'Status', 'IssueDate_Display', 'PaymentDate_Display']
                        cols_invoices_filtered = [col for col in cols_invoices if col in invoices_df.columns]
                        st.dataframe(invoices_df[cols_invoices_filtered], use_container_width=True, hide_index=True)
                        
                        if 'TotalAmount' in invoices_df.columns and 'Status' in invoices_df.columns:
                            paid_invoices_sum = invoices_df.loc[invoices_df['Status'] == 'Paid', 'TotalAmount'].sum()
                            total_invoiced_amount = paid_invoices_sum if pd.notnull(paid_invoices_sum) else 0.0
                        st.metric("Total Amount from Paid Invoices for this Customer", f"Rs. {total_invoiced_amount:,.2f}")
                    else:
                        st.info("No invoices found for this customer.")

                    st.markdown("---")
                    st.markdown("### Associated Projects")
                    customer_projects_rows = db.get_projects_by_customer_id(cust_id)
                    customer_projects = db.rows_to_dicts(customer_projects_rows) if customer_projects_rows else []
                    if customer_projects:
                        projects_df = pd.DataFrame(customer_projects)
                        projects_df['Budget_Display'] = projects_df['Budget'].apply(lambda x: f"Rs. {x:,.2f}" if pd.notnull(x) else "Rs. 0.00")
                        cols_projects = ['ProjectID', 'ProjectName', 'Status', 'StartDate', 'EndDate', 'Budget_Display']
                        cols_projects_filtered = [col for col in cols_projects if col in projects_df.columns]
                        st.dataframe(projects_df[cols_projects_filtered], use_container_width=True, hide_index=True)
                    else:
                        st.info("No projects associated with this customer.")
                else:
                    st.warning("Could not process customer data. The customer may have been deleted or data is malformed.")
                    st.session_state.customer_management_action_view = "List"
                    st.session_state.selected_customer_id_for_detail_view = None
                    st.rerun() 
            else:
                st.warning("Could not fetch customer data (customer might be deleted).")
                st.session_state.customer_management_action_view = "List"
                st.session_state.selected_customer_id_for_detail_view = None
                st.rerun() 
        else:
            st.info("No customer selected for details. Please select one from the list.")
            st.session_state.customer_management_action_view = "List" 
            st.rerun()

elif choice == "Supplier Management":
    # ... (Supplier Management code as before, ensure get_supplier_by_id returns dict or handle row[0]) ...
    st.header("🚚 Supplier Management")
    action_sup = st.selectbox("Action", ["View All", "Add New", "Edit Supplier", "Delete Supplier"], key="sup_action")

    if action_sup == "View All":
        st.subheader("Existing Suppliers")
        search_term_sup = st.text_input("Search Suppliers (Name, Contact, Email)", key="search_sup_view")
        suppliers_list_rows = db.get_all_suppliers(search_term=search_term_sup)
        if suppliers_list_rows:
            st.dataframe(db.rows_to_dicts(suppliers_list_rows), use_container_width=True, hide_index=True)
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
        suppliers_list_edit_rows = db.get_all_suppliers()
        if not suppliers_list_edit_rows:
            st.info("No suppliers to edit.")
        else:
            suppliers_list_edit = db.rows_to_dicts(suppliers_list_edit_rows)
            supplier_options = {f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_list_edit}
            selected_sup_disp = st.selectbox("Select Supplier", list(supplier_options.keys()), key="edit_sup_select", index=None, placeholder="Select a supplier...")
            if selected_sup_disp:
                sup_id_to_edit = supplier_options[selected_sup_disp]
                sup_data_row = db.get_supplier_by_id(sup_id_to_edit) # Expects single row
                sup_data = dict(sup_data_row) if sup_data_row else None
                if sup_data:
                    with st.form(f"edit_supplier_form_{sup_id_to_edit}"):
                        st.write(f"Editing Supplier ID: {sup_data['SupplierID']}")
                        s_name = st.text_input("Supplier Name*", value=sup_data.get('SupplierName',''))
                        s_contact = st.text_input("Contact Person", value=sup_data.get('ContactPerson',''))
                        s_email = st.text_input("Email", value=sup_data.get('Email',''))
                        s_phone = st.text_input("Phone", value=sup_data.get('Phone',''))
                        s_address = st.text_area("Address", value=sup_data.get('Address',''))
                        updated = st.form_submit_button("Update Supplier")
                        if updated:
                            if not s_name: st.error("Supplier Name is required.")
                            else:
                                try:
                                    db.update_supplier(sup_id_to_edit, s_name, s_contact, s_email, s_phone, s_address)
                                    st.success("Supplier updated!")
                                    st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
                else:
                    st.error(f"Could not load data for supplier ID {sup_id_to_edit}")


    elif action_sup == "Delete Supplier":
        st.subheader("Delete Supplier")
        suppliers_list_del_rows = db.get_all_suppliers()
        if not suppliers_list_del_rows: st.info("No suppliers to delete.")
        else:
            suppliers_list_del = db.rows_to_dicts(suppliers_list_del_rows)
            supplier_options_del = {f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_list_del}
            selected_sup_disp_del = st.selectbox("Select Supplier to Delete", list(supplier_options_del.keys()), key="del_sup_select", index=None, placeholder="Select a supplier...")
            if selected_sup_disp_del:
                sup_id_to_del = supplier_options_del[selected_sup_disp_del]
                st.warning(f"Are you sure you want to delete {selected_sup_disp_del}? This may affect product/material/service records by setting their supplier to 'None'.")
                if st.button("Confirm Delete", key=f"confirm_del_sup_{sup_id_to_del}"):
                    try:
                        db.delete_supplier(sup_id_to_del)
                        st.success(f"Supplier {selected_sup_disp_del} deleted!")
                        st.rerun()
                    except Exception as e: st.error(f"Error deleting supplier: {e}")


elif choice == "Supplier Services":
    # ... (Supplier Services code as before, ensure get_supplier_service_by_id returns dict or handle row[0]) ...
    st.header("🛠️ Supplier Services Management")
    action_ss = st.selectbox("Action", ["View All Services", "Add New Service", "Edit Service", "Delete Service"], key="ss_action")

    all_suppliers_ss_rows = db.get_all_suppliers()
    all_suppliers_ss = db.rows_to_dicts(all_suppliers_ss_rows) if all_suppliers_ss_rows else []
    supplier_map_ss = {"Select Supplier*": None}
    supplier_map_ss.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in all_suppliers_ss})

    all_projects_ss_rows = db.get_all_projects()
    all_projects_ss = db.rows_to_dicts(all_projects_ss_rows) if all_projects_ss_rows else []
    project_map_ss = {"None (General Service)": None}
    project_map_ss.update({f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in all_projects_ss})

    service_type_options = ["Paint Work", "Wood Cutting", "Polishing", "Stitching", "Assembly", "Transportation", "Consultation", "Other"]

    if action_ss == "View All Services":
        st.subheader("Recorded Supplier Services")
        search_term_ss = st.text_input("Search Services (Name, Type, Supplier, Project, Desc.)", key="search_ss_view")
        services_list_rows = db.get_all_supplier_services(search_term=search_term_ss)
        services_list = db.rows_to_dicts(services_list_rows) if services_list_rows else []
        if services_list:
            df_services = pd.DataFrame(services_list)
            if 'Cost' in df_services.columns:
                 df_services['Cost_Display'] = df_services['Cost'].apply(lambda x: f"Rs. {x:,.2f}")

            cols_to_show = ['ServiceID', 'ServiceName', 'ServiceType', 'SupplierName', 'ProjectName',
                            'ServiceDate', 'Cost_Display', 'Description', 'IsExpenseLogged']
            cols_to_show_filtered = [col for col in cols_to_show if col in df_services.columns]
            st.dataframe(df_services[cols_to_show_filtered], use_container_width=True, hide_index=True)

            for service_row_dict in services_list: 
                if service_row_dict.get('ReceiptPath') and os.path.exists(service_row_dict['ReceiptPath']):
                    with st.expander(f"View Receipt for Service ID: {service_row_dict['ServiceID']}"):
                        try:
                            if service_row_dict['ReceiptPath'].lower().endswith(('.png', '.jpg', '.jpeg')):
                                receipt_image = Image.open(service_row_dict['ReceiptPath'])
                                st.image(receipt_image, caption=f"Receipt for {service_row_dict['ServiceName']}", width=300)
                            else:
                                with open(service_row_dict['ReceiptPath'], "rb") as fp:
                                    st.download_button(
                                        label=f"Download Receipt ({os.path.basename(service_row_dict['ReceiptPath'])})",
                                        data=fp,
                                        file_name=os.path.basename(service_row_dict['ReceiptPath']),
                                        mime="application/octet-stream"
                                    )
                        except Exception as e:
                            st.warning(f"Could not load/display receipt: {e}")
        else:
            st.info("No supplier services recorded yet.")

    elif action_ss == "Add New Service":
        st.subheader("Add New Supplier Service")
        with st.form("add_supplier_service_form", clear_on_submit=True):
            selected_supplier_name_ss = st.selectbox("Supplier*", list(supplier_map_ss.keys()), key="add_ss_supplier", index=0)
            ss_supplier_id = supplier_map_ss.get(selected_supplier_name_ss)

            selected_project_name_ss = st.selectbox("Associated Project (Optional)", list(project_map_ss.keys()), key="add_ss_project", index=0)
            ss_project_id = project_map_ss.get(selected_project_name_ss)

            ss_service_name = st.text_input("Service Name/Title*", help="e.g., Custom painting for chair X, Polishing dining table set")
            ss_service_type_selected = st.selectbox("Service Type*", service_type_options, key="add_ss_type")
            ss_service_type_final = ss_service_type_selected
            if ss_service_type_selected == "Other":
                ss_service_type_other = st.text_input("Specify Other Service Type", key="add_ss_type_other")
                if ss_service_type_other.strip(): ss_service_type_final = ss_service_type_other.strip()


            ss_service_date = st.date_input("Service Date*", datetime.now().date())
            ss_cost = st.number_input("Service Cost (Rs.)*", min_value=0.0, format="%.2f")
            ss_receipt_upload = st.file_uploader("Upload Receipt (Optional)", type=['png', 'jpg', 'jpeg', 'pdf'])
            ss_description = st.text_area("Description/Notes")

            submitted = st.form_submit_button("Add Service")
            if submitted:
                if not ss_supplier_id or not ss_service_name or not ss_service_type_final or ss_cost < 0: 
                    st.error("Supplier, Service Name, Service Type, and a valid Cost are required.")
                else:
                    try:
                        new_service_id, expense_auto_logged = db.add_supplier_service(
                            ss_supplier_id, ss_project_id, ss_service_name, ss_service_type_final,
                            ss_service_date.strftime("%Y-%m-%d"), ss_cost,
                            None, 
                            ss_description
                        )

                        if new_service_id and ss_receipt_upload:
                            receipt_file_path = save_uploaded_receipt(ss_receipt_upload, new_service_id)
                            if receipt_file_path:
                                db.update_supplier_service_receipt_path(new_service_id, receipt_file_path) # Assuming a dedicated function
                                st.success(f"Service (ID: {new_service_id}) added with receipt!")
                            else:
                                st.warning(f"Service (ID: {new_service_id}) added, but receipt upload failed.")
                        elif new_service_id:
                             st.success(f"Service (ID: {new_service_id}) added!")

                        if expense_auto_logged:
                            st.info("This service cost has been automatically logged as an expense.")
                        elif new_service_id and ss_cost > 0: 
                            st.warning("Service added. If an expense was expected to be auto-logged, please verify in Expense Tracking.")

                    except Exception as e:
                        st.error(f"Error adding service: {e}")

    elif action_ss == "Edit Service":
        st.subheader("Edit Supplier Service")
        services_list_edit_rows = db.get_all_supplier_services()
        services_list_edit = db.rows_to_dicts(services_list_edit_rows) if services_list_edit_rows else []
        if not services_list_edit: st.info("No services to edit.")
        else:
            service_options = {f"{s['ServiceName']} by {s.get('SupplierName', 'N/A')} (ID: {s['ServiceID']})": s['ServiceID'] for s in services_list_edit} 
            selected_service_disp = st.selectbox("Select Service to Edit", list(service_options.keys()), key="edit_ss_select", index=None, placeholder="Select a service...")

            if selected_service_disp:
                service_id_to_edit = service_options[selected_service_disp]
                service_data_row = db.get_supplier_service_by_id(service_id_to_edit) # Expects single row
                service_data = dict(service_data_row) if service_data_row else None
                
                if service_data:
                    with st.form(f"edit_supplier_service_form_{service_id_to_edit}"):
                        # ... (rest of the edit form, similar to before but using service_data directly)
                        st.write(f"Editing Service ID: {service_data['ServiceID']}")

                        current_supplier_id_ss = service_data['SupplierID']
                        supplier_keys_list = list(supplier_map_ss.keys())
                        try:
                            supplier_index = supplier_keys_list.index(next(k for k,v in supplier_map_ss.items() if v == current_supplier_id_ss))
                        except (StopIteration, ValueError): supplier_index = 0 
                        selected_supplier_name_ss_edit = st.selectbox("Supplier*", supplier_keys_list, index=supplier_index, key=f"edit_ss_supplier_{service_id_to_edit}")
                        ss_supplier_id_edit = supplier_map_ss.get(selected_supplier_name_ss_edit)

                        current_project_id_ss = service_data.get('ProjectID') 
                        project_keys_list = list(project_map_ss.keys())
                        try:
                            project_index = project_keys_list.index(next(k for k,v in project_map_ss.items() if v == current_project_id_ss))
                        except (StopIteration, ValueError): project_index = 0
                        selected_project_name_ss_edit = st.selectbox("Associated Project (Optional)", project_keys_list, index=project_index, key=f"edit_ss_project_{service_id_to_edit}")
                        ss_project_id_edit = project_map_ss.get(selected_project_name_ss_edit)

                        ss_service_name_edit = st.text_input("Service Name/Title*", value=service_data.get('ServiceName',''))

                        current_service_type_edit_val = service_data.get('ServiceType','')
                        ss_service_type_form_val = current_service_type_edit_val if current_service_type_edit_val in service_type_options else "Other"
                        
                        try:
                            ss_service_type_form_index = service_type_options.index(ss_service_type_form_val)
                        except ValueError:
                            ss_service_type_form_index = service_type_options.index("Other") # Default to other if not found

                        ss_service_type_selected_edit = st.selectbox("Service Type*", service_type_options, index=ss_service_type_form_index, key=f"edit_ss_type_sel_{service_id_to_edit}")
                        
                        ss_service_type_other_val_edit = current_service_type_edit_val if ss_service_type_form_val == "Other" and current_service_type_edit_val not in service_type_options else ""
                        ss_service_type_other_input_edit = st.text_input("Specify Other Service Type", value=ss_service_type_other_val_edit, key=f"edit_ss_type_other_input_{service_id_to_edit}")

                        ss_service_type_final_edit = ss_service_type_selected_edit
                        if ss_service_type_selected_edit == "Other" and ss_service_type_other_input_edit.strip():
                             ss_service_type_final_edit = ss_service_type_other_input_edit.strip()

                        ss_service_date_val = datetime.strptime(service_data['ServiceDate'], "%Y-%m-%d").date() if service_data.get('ServiceDate') else datetime.now().date()
                        ss_service_date_edit = st.date_input("Service Date*", value=ss_service_date_val)
                        ss_cost_edit = st.number_input("Service Cost (Rs.)*", value=float(service_data.get('Cost', 0.0)), min_value=0.0, format="%.2f")
                        ss_is_expense_logged_edit = bool(service_data.get('IsExpenseLogged', False))

                        st.write("Current Receipt:")
                        current_receipt_path = service_data.get('ReceiptPath')
                        if current_receipt_path and os.path.exists(current_receipt_path):
                            if current_receipt_path.lower().endswith(('.png','.jpg','.jpeg')):
                                st.image(Image.open(current_receipt_path), width=150)
                            else:
                                st.download_button(label=f"Download Current Receipt", data=open(current_receipt_path, "rb").read(), file_name=os.path.basename(current_receipt_path), mime="application/octet-stream", key=f"dl_btn_{service_id_to_edit}" )
                        else: st.text("No receipt on file.")

                        ss_new_receipt_upload = st.file_uploader("Upload New Receipt (Optional - replaces old)", type=['png', 'jpg', 'jpeg', 'pdf'], key=f"edit_ss_receipt_{service_id_to_edit}")
                        ss_description_edit = st.text_area("Description/Notes", value=service_data.get('Description', ''))

                        updated = st.form_submit_button("Update Service")
                        if updated:
                            if not ss_supplier_id_edit or not ss_service_name_edit or not ss_service_type_final_edit or ss_cost_edit < 0:
                                st.error("Supplier, Name, Type, Cost are required.")
                            else:
                                receipt_path_to_save = current_receipt_path
                                if ss_new_receipt_upload:
                                    if current_receipt_path and os.path.exists(current_receipt_path):
                                        try: os.remove(current_receipt_path)
                                        except Exception as e_del: st.warning(f"Could not remove old receipt {current_receipt_path}: {e_del}")
                                    receipt_path_to_save = save_uploaded_receipt(ss_new_receipt_upload, service_id_to_edit)

                                try:
                                    # Pass the existing IsExpenseLogged state to the update function
                                    db.update_supplier_service(
                                        service_id_to_edit, ss_supplier_id_edit, ss_project_id_edit, ss_service_name_edit,
                                        ss_service_type_final_edit, ss_service_date_edit.strftime("%Y-%m-%d"), ss_cost_edit,
                                        receipt_path_to_save, ss_description_edit, ss_is_expense_logged_edit 
                                    )
                                    st.success("Service updated! Note: If cost or critical details changed, associated expense may need manual review/adjustment if it was auto-logged.")
                                    st.rerun()
                                except Exception as e: st.error(f"Error updating service: {e}")
                else:
                    st.error(f"Could not load data for service ID {service_id_to_edit}")

    elif action_ss == "Delete Service":
        st.subheader("Delete Supplier Service")
        services_list_del_rows = db.get_all_supplier_services()
        services_list_del = db.rows_to_dicts(services_list_del_rows) if services_list_del_rows else []
        if not services_list_del: st.info("No services to delete.")
        else:
            service_options_del = {f"{s['ServiceName']} by {s.get('SupplierName','N/A')} (ID: {s['ServiceID']})": s['ServiceID'] for s in services_list_del}
            selected_service_disp_del = st.selectbox("Select Service to Delete", list(service_options_del.keys()), key="del_ss_select", index=None, placeholder="Select a service...")
            if selected_service_disp_del:
                service_id_to_del = service_options_del[selected_service_disp_del]
                st.warning(f"Are you sure you want to delete this service (ID: {service_id_to_del})? This will also delete its receipt file. The auto-logged expense will NOT be automatically deleted and may require manual action.")
                if st.button("Confirm Delete", key=f"confirm_del_ss_{service_id_to_del}"):
                    try:
                        db.delete_supplier_service(service_id_to_del) 
                        st.success("Service deleted successfully!")
                        st.rerun()
                    except Exception as e: st.error(f"Error deleting service: {e}")

elif choice == "Material Management":
    # ... (Material Management code as before, ensure get_material_by_id returns dict or handle row[0]) ...
    # ... and ensure Materials table has Category and SupplierID ...
    st.header("🧱 Material Management")
    action_mat = st.selectbox("Action", ["View All", "Add New", "Edit Material", "Delete Material"], key="mat_action")
    
    suppliers_for_mat_rows = db.get_all_suppliers()
    suppliers_for_mat = db.rows_to_dicts(suppliers_for_mat_rows) if suppliers_for_mat_rows else []
    supplier_map_mat = {"None (No Supplier)": None}
    supplier_map_mat.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_for_mat})

    if action_mat == "View All":
        st.subheader("Existing Materials")
        search_term_mat = st.text_input("Search Materials (Name, Category, Supplier)", key="search_mat_view") # Changed Type to Category
        materials_list_rows = db.get_all_materials(search_term=search_term_mat) # Assumes get_all_materials can search by Category
        if materials_list_rows: 
            df_materials = pd.DataFrame(db.rows_to_dicts(materials_list_rows))
            # Ensure columns like SupplierName are present if expected from db function
            cols_to_show_mat = [col for col in df_materials.columns if col != 'SupplierID'] # Example: hide raw ID if name shown
            st.dataframe(df_materials[cols_to_show_mat], use_container_width=True, hide_index=True)
        else: 
            st.info("No materials found.")

    elif action_mat == "Add New":
        st.subheader("Add New Material")
        with st.form("add_material_form_page", clear_on_submit=True):
            m_name = st.text_input("Material Name*")
            m_category = st.text_input("Category (e.g., Wood, Fabric, Finishing)") # Changed from m_type
            m_subtype = st.text_input("Sub-Type (e.g., Oak, Velvet, Varnish) (Optional)")
            m_unit = st.text_input("Unit of Measure (e.g., m, kg, piece)")
            m_cost_unit = st.number_input("Cost Per Unit (Rs.)", min_value=0.0, format="%.2f")
            m_qty = st.number_input("Quantity In Stock", format="%.2f", min_value=0.0)
            selected_sup_name_mat = st.selectbox("Primary Supplier (Optional)", list(supplier_map_mat.keys()), key="add_mat_supplier_page", index=0) 
            m_supplier_id = supplier_map_mat.get(selected_sup_name_mat)
            submitted = st.form_submit_button("Add Material")
            if submitted:
                if not m_name: st.error("Material Name required.")
                else:
                    try:
                        # db.add_material needs to accept category and subtype
                        db.add_material(m_name, m_category, m_subtype, m_unit, m_cost_unit, m_qty, m_supplier_id)
                        st.success("Material added!")
                    except Exception as e: st.error(f"Error: {e}")

    elif action_mat == "Edit Material":
        st.subheader("Edit Material")
        materials_list_edit_rows = db.get_all_materials()
        if not materials_list_edit_rows: 
            st.info("No materials to edit.")
        else:
            materials_list_edit = db.rows_to_dicts(materials_list_edit_rows)
            material_options = {f"{m['MaterialName']} (ID: {m['MaterialID']})": m['MaterialID'] for m in materials_list_edit}
            selected_mat_disp = st.selectbox("Select Material", list(material_options.keys()), key="edit_mat_select_page", index=None, placeholder="Select a material...")
            if selected_mat_disp:
                mat_id_to_edit = material_options[selected_mat_disp]
                mat_data_row = db.get_material_by_id(mat_id_to_edit) # Expects single row
                mat_data = dict(mat_data_row) if mat_data_row else None
                if mat_data:
                    with st.form(f"edit_material_form_page_{mat_id_to_edit}"):
                        m_name = st.text_input("Material Name*", value=mat_data.get('MaterialName',''))
                        m_category = st.text_input("Category", value=mat_data.get('Category','')) # Changed from MaterialType
                        m_subtype = st.text_input("Sub-Type", value=mat_data.get('SubType',''))
                        m_unit = st.text_input("Unit of Measure", value=mat_data.get('UnitOfMeasure',''))
                        m_cost_unit = st.number_input("Cost Per Unit (Rs.)", value=float(mat_data.get('CostPerUnit',0.0)), min_value=0.0, format="%.2f")
                        m_qty = st.number_input("Quantity In Stock", value=float(mat_data.get('QuantityInStock',0.0)), format="%.2f", min_value=0.0)
                        current_supplier_id = mat_data.get('SupplierID')
                        material_supplier_keys_list = list(supplier_map_mat.keys())
                        try: 
                            mat_supplier_index = material_supplier_keys_list.index(next(k for k,v in supplier_map_mat.items() if v == current_supplier_id))
                        except (StopIteration, ValueError): 
                            mat_supplier_index = 0 
                        selected_sup_name_mat_edit = st.selectbox("Primary Supplier (Optional)", material_supplier_keys_list, index=mat_supplier_index, key="edit_mat_supplier_page") 
                        m_supplier_id_edit = supplier_map_mat.get(selected_sup_name_mat_edit)
                        updated = st.form_submit_button("Update Material")
                        if updated:
                            if not m_name: st.error("Material Name required.")
                            else:
                                try:
                                    # db.update_material needs to accept category and subtype
                                    db.update_material(mat_id_to_edit, m_name, m_category, m_subtype, m_unit, m_cost_unit, m_qty, m_supplier_id_edit)
                                    st.success("Material updated!")
                                    st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
                else:
                    st.error(f"Could not load data for material ID {mat_id_to_edit}")

    elif action_mat == "Delete Material":
        st.subheader("Delete Material")
        materials_list_del_rows = db.get_all_materials()
        if not materials_list_del_rows: 
            st.info("No materials to delete.")
        else:
            materials_list_del = db.rows_to_dicts(materials_list_del_rows)
            material_options_del = {f"{m['MaterialName']} (ID: {m['MaterialID']})": m['MaterialID'] for m in materials_list_del}
            selected_mat_disp_del = st.selectbox("Select Material to Delete", list(material_options_del.keys()), key="del_mat_select_page", index=None, placeholder="Select a material...") 
            if selected_mat_disp_del:
                mat_id_to_del = material_options_del[selected_mat_disp_del]
                st.warning(f"Are you sure you want to delete {selected_mat_disp_del}? This material might be used in existing project records (ProjectMaterials table), potentially causing issues or breaking links if not handled by DB constraints (e.g., ON DELETE SET NULL).")
                if st.button("Confirm Delete", key=f"confirm_del_mat_page_{mat_id_to_del}"): 
                    try:
                        db.delete_material(mat_id_to_del)
                        st.success(f"Material {selected_mat_disp_del} deleted!")
                        st.rerun()
                    except Exception as e: st.error(f"Error deleting material: {e}. Check if it's linked in projects.")


elif choice == "Product Management":
    # ... (Product Management code as before, ensure get_product_by_id returns dict or handle row[0]) ...
    # ... and ensure Product table has 'MaterialType' if used, distinct from Material's 'Category' ...
    st.header("📦 Product Management (Inventory)")
    action_prod = st.selectbox("Action", ["View All", "Add New", "Edit Product", "Delete Product"], key="prod_action_key_main")
    
    suppliers_for_prod_rows = db.get_all_suppliers()
    suppliers_for_prod = db.rows_to_dicts(suppliers_for_prod_rows) if suppliers_for_prod_rows else []
    supplier_map_prod = {"None (No Supplier)": None}
    supplier_map_prod.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_for_prod})

    if action_prod == "View All":
        st.subheader("Existing Products")
        search_term_prod = st.text_input("Search Products (Name, SKU, Category, Supplier)", key="search_prod_view_main")
        products_list_rows = db.get_all_products(search_term=search_term_prod) # Assumes get_all_products joins with suppliers for SupplierName
        if products_list_rows:
            products_list = db.rows_to_dicts(products_list_rows)
            df_products = pd.DataFrame(products_list)
            
            final_cols_prod_view = []
            default_prod_cols = ['ProductID', 'ProductName', 'SKU', 'Category', 'SellingPrice', 'QuantityInStock', 'SupplierName', 'Description', 'MaterialType', 'Dimensions', 'CostPrice', 'ReorderLevel']
            for col in default_prod_cols:
                if col in df_products.columns:
                    final_cols_prod_view.append(col)
            for col in df_products.columns: # Add any other existing columns not explicitly listed or in ImagePath/SupplierID
                if col not in final_cols_prod_view and col not in ['ImagePath', 'SupplierID']:
                     final_cols_prod_view.append(col)

            st.dataframe(df_products[final_cols_prod_view], use_container_width=True, hide_index=True)

            for prod_row_dict_main in products_list: 
                if prod_row_dict_main.get('ImagePath') and os.path.exists(prod_row_dict_main['ImagePath']):
                    with st.expander(f"{prod_row_dict_main['ProductName']} - Image"):
                        try: 
                            st.image(Image.open(prod_row_dict_main['ImagePath']), caption=prod_row_dict_main['ProductName'], width=200)
                        except Exception as e_img: 
                            st.warning(f"Could not load image for {prod_row_dict_main['ProductName']}: {e_img}")
        else: 
            st.info("No products found.")
            
    elif action_prod == "Add New":
        st.subheader("Add New Product")
        with st.form("add_product_form_main", clear_on_submit=False): 
            p_name = st.text_input("Product Name*")
            p_sku = st.text_input("SKU (Unique)")
            p_desc = st.text_area("Description")
            p_cat = st.text_input("Category (e.g., Sofa, Table)")
            p_mat_type_prod = st.text_input("Primary Material Type (e.g., Wood, Fabric)") 
            p_dims = st.text_input("Dimensions (L x W x H)")
            p_cost = st.number_input("Cost Price (Rs.)", min_value=0.0, format="%.2f")
            p_sell = st.number_input("Selling Price (Rs.)", min_value=0.0, format="%.2f")
            p_qty = st.number_input("Quantity In Stock", min_value=0, step=1)
            p_reorder = st.number_input("Reorder Level", min_value=0, step=1)
            selected_sup_name_prod_add = st.selectbox("Supplier (if applicable)", list(supplier_map_prod.keys()), key="add_prod_supplier_main", index=0)
            p_supplier_id_add = supplier_map_prod.get(selected_sup_name_prod_add)
            p_uploaded_image_add = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"], key="add_prod_img_main")
            submitted_add_prod = st.form_submit_button("Add Product")
            if submitted_add_prod:
                if not p_name or not p_sku: 
                    st.error("Product Name and SKU required.")
                else:
                    p_image_path_add = None
                    if p_uploaded_image_add: 
                        p_image_path_add = save_uploaded_product_image(p_uploaded_image_add, p_sku)
                    try:
                        db.add_product(p_name, p_sku, p_desc, p_cat, p_mat_type_prod, p_dims, p_cost, p_sell, p_qty, p_reorder, p_supplier_id_add, p_image_path_add)
                        st.success(f"Product '{p_name}' added!")
                        st.rerun() 
                    except Exception as e_add_prod:
                        st.error(f"Error adding product: {e_add_prod}")
                        if p_image_path_add and os.path.exists(p_image_path_add): 
                            try: os.remove(p_image_path_add) 
                            except OSError as e_os_remove: st.warning(f"Failed to remove uploaded image after error: {e_os_remove}")

    elif action_prod == "Edit Product":
        st.subheader("Edit Product")
        products_list_edit_rows = db.get_all_products()
        if not products_list_edit_rows: 
            st.info("No products to edit.")
        else:
            products_list_edit_main = db.rows_to_dicts(products_list_edit_rows)
            product_options_edit_main = {f"{p['ProductName']} (SKU: {p.get('SKU','N/A')}, ID: {p['ProductID']})": p['ProductID'] for p in products_list_edit_main}
            selected_prod_disp_edit_main = st.selectbox("Select Product to Edit", list(product_options_edit_main.keys()), key="edit_prod_select_key_main_page", index=None, placeholder="Select a product...")
            if selected_prod_disp_edit_main:
                prod_id_to_edit_main = product_options_edit_main[selected_prod_disp_edit_main]
                prod_data_row = db.get_product_by_id(prod_id_to_edit_main) # Expects single row
                prod_data_edit_main = dict(prod_data_row) if prod_data_row else None
                
                if prod_data_edit_main:
                    with st.form(f"edit_product_form_main_page_{prod_id_to_edit_main}"):
                        p_name_edit = st.text_input("Product Name*", value=prod_data_edit_main.get('ProductName',''))
                        p_sku_edit = st.text_input("SKU (Unique)", value=prod_data_edit_main.get('SKU',''), help="Changing SKU might affect image linkage if SKU is part of filename.")
                        p_desc_edit = st.text_area("Description", value=prod_data_edit_main.get('Description',''))
                        p_cat_edit = st.text_input("Category", value=prod_data_edit_main.get('Category',''))
                        p_mat_type_prod_edit = st.text_input("Primary Material Type", value=prod_data_edit_main.get('MaterialType',''))
                        p_dims_edit = st.text_input("Dimensions", value=prod_data_edit_main.get('Dimensions',''))
                        p_cost_edit = st.number_input("Cost Price (Rs.)", value=float(prod_data_edit_main.get('CostPrice',0.0)), min_value=0.0, format="%.2f")
                        p_sell_edit = st.number_input("Selling Price (Rs.)", value=float(prod_data_edit_main.get('SellingPrice',0.0)), min_value=0.0, format="%.2f")
                        p_qty_edit = st.number_input("Quantity In Stock", value=int(prod_data_edit_main.get('QuantityInStock',0)), min_value=0, step=1)
                        p_reorder_edit = st.number_input("Reorder Level", value=int(prod_data_edit_main.get('ReorderLevel',0)), min_value=0, step=1)
                        
                        current_sup_id_prod_edit = prod_data_edit_main.get('SupplierID')
                        product_supplier_keys_list = list(supplier_map_prod.keys())
                        try: 
                            prod_supplier_index = product_supplier_keys_list.index(next(k for k,v in supplier_map_prod.items() if v == current_sup_id_prod_edit))
                        except (StopIteration,ValueError): 
                            prod_supplier_index = 0
                        selected_sup_name_prod_edit_page = st.selectbox("Supplier", product_supplier_keys_list, index=prod_supplier_index, key="edit_prod_supplier_main_page")
                        p_supplier_id_edit = supplier_map_prod.get(selected_sup_name_prod_edit_page)
                        
                        st.write("Current Image:")
                        current_image_path_edit = prod_data_edit_main.get('ImagePath')
                        if current_image_path_edit and os.path.exists(current_image_path_edit):
                            try: 
                                st.image(Image.open(current_image_path_edit), width=150)
                            except Exception: 
                                st.text("Could not load current image.")
                        else: 
                            st.text("No image on file.")
                            
                        p_new_uploaded_image_edit = st.file_uploader("Upload New Image (Optional - replaces old)", type=["png", "jpg", "jpeg"], key=f"edit_img_upload_main_page_{prod_id_to_edit_main}")
                        
                        updated_prod = st.form_submit_button("Update Product")
                        if updated_prod:
                            if not p_name_edit or not p_sku_edit: 
                                st.error("Name and SKU required.")
                            else:
                                image_path_to_save_edit = current_image_path_edit
                                if p_new_uploaded_image_edit:
                                    new_image_filename_base = p_sku_edit 
                                    if current_image_path_edit and os.path.exists(current_image_path_edit):
                                        try: 
                                            os.remove(current_image_path_edit)
                                            st.caption(f"Old image {os.path.basename(current_image_path_edit)} removed.")
                                        except Exception as e_del_img: 
                                            st.warning(f"Old image removal issue: {e_del_img}")
                                    image_path_to_save_edit = save_uploaded_product_image(p_new_uploaded_image_edit, new_image_filename_base)
                                try:
                                    db.update_product(prod_id_to_edit_main, p_name_edit, p_sku_edit, p_desc_edit, p_cat_edit, p_mat_type_prod_edit, p_dims_edit, p_cost_edit, p_sell_edit, p_qty_edit, p_reorder_edit, p_supplier_id_edit, image_path_to_save_edit)
                                    st.success("Product updated!")
                                    st.rerun()
                                except Exception as e_upd_prod: 
                                    st.error(f"Error updating: {e_upd_prod}")
                else:
                    st.error(f"Could not load data for product ID {prod_id_to_edit_main}")

    elif action_prod == "Delete Product":
        st.subheader("Delete Product")
        products_list_del_rows = db.get_all_products()
        if not products_list_del_rows: 
            st.info("No products to delete.")
        else:
            products_list_del_main = db.rows_to_dicts(products_list_del_rows)
            product_options_del_main = {f"{p['ProductName']} (SKU: {p.get('SKU','N/A')}, ID: {p['ProductID']})": p['ProductID'] for p in products_list_del_main}
            selected_prod_disp_del_main = st.selectbox("Select Product to Delete", list(product_options_del_main.keys()), key="del_prod_select_key_main_page", index=None, placeholder="Select a product...")
            if selected_prod_disp_del_main:
                prod_id_to_del_main = product_options_del_main[selected_prod_disp_del_main]
                st.warning(f"Are you sure you want to delete {selected_prod_disp_del_main}? This cannot be undone and will also delete its image file (if linked and db.delete_product handles it).")
                if st.button("Confirm Delete", key=f"confirm_del_prod_main_page_{prod_id_to_del_main}"):
                    try:
                        db.delete_product(prod_id_to_del_main) 
                        st.success("Product deleted successfully!")
                        st.rerun()
                    except Exception as e_del_prod_main: 
                        st.error(f"Error deleting product: {e_del_prod_main}")


elif choice == "Project Management":
    st.header("🛠️ Project Management")
    action_proj = st.selectbox("Action", ["View All", "Add New", "Edit Project", "Delete Project"], key="proj_action_main_key")
    
    customers_for_proj_rows = db.get_all_customers()
    customers_for_proj = db.rows_to_dicts(customers_for_proj_rows) if customers_for_proj_rows else []
    customer_map_proj = {"Select Customer*": None} 
    customer_map_proj.update({f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_proj})
    
    project_status_options = ["Planning", "In Progress", "On Hold", "Completed", "Cancelled"]

    if action_proj == "View All":
        st.subheader("Existing Projects")
        search_term_proj = st.text_input("Search Projects (Name, Customer, Status)", key="search_proj_view_main_key")
        projects_list_rows = db.get_all_projects(search_term=search_term_proj) 
        if projects_list_rows:
            projects_list = db.rows_to_dicts(projects_list_rows)
            df_projects = pd.DataFrame(projects_list)
            if 'Budget' in df_projects.columns:
                df_projects['Budget_Display'] = df_projects['Budget'].apply(lambda x: f"Rs. {x:,.2f}" if pd.notnull(x) else "N/A")
            
            cols_to_show = ['ProjectID', 'ProjectName', 'CustomerName', 'StartDate', 'EndDate', 'Status', 'Budget_Display', 'Description']
            cols_filtered = [col for col in cols_to_show if col in df_projects.columns]
            st.dataframe(df_projects[cols_filtered], use_container_width=True, hide_index=True)
        else:
            st.info("No projects found.")

    elif action_proj == "Add New":
        st.subheader("Add New Project")
        with st.form("add_project_form_main_key", clear_on_submit=True):
            pr_name = st.text_input("Project Name*")
            selected_cust_name_proj = st.selectbox("Customer*", list(customer_map_proj.keys()), index=0, key="add_proj_customer_main_key") 
            pr_customer_id = customer_map_proj.get(selected_cust_name_proj)
            
            col_start_proj, col_end_proj = st.columns(2)
            pr_start_date = col_start_proj.date_input("Start Date", datetime.now().date())
            pr_end_date = col_end_proj.date_input("Expected End Date", (datetime.now() + timedelta(days=30)).date() )
            pr_status = st.selectbox("Status", project_status_options)
            pr_budget = st.number_input("Budget (Rs.)", min_value=0.0, format="%.2f")
            pr_desc = st.text_area("Description")
            submitted_proj = st.form_submit_button("Add Project")
            if submitted_proj:
                if not pr_name: 
                    st.error("Project Name required.")
                elif not pr_customer_id: 
                    st.error("Customer is required for a project.")
                else:
                    try:
                        db.add_project(pr_name, pr_customer_id, 
                                       pr_start_date.strftime("%Y-%m-%d") if pr_start_date else None, 
                                       pr_end_date.strftime("%Y-%m-%d") if pr_end_date else None, 
                                       pr_status, pr_budget, pr_desc)
                        st.success("Project added!")
                    except Exception as e_proj_add: 
                        st.error(f"Error adding project: {e_proj_add}")

    elif action_proj == "Edit Project":
        st.subheader("Edit Project")
        projects_list_edit_rows = db.get_all_projects()
        if not projects_list_edit_rows: 
            st.info("No projects to edit.")
        else:
            projects_list_edit_main = db.rows_to_dicts(projects_list_edit_rows)
            project_options_edit_main_page = {f"{p.get('ProjectName','Unnamed Project')} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_list_edit_main}
            selected_proj_disp_edit_main_page = st.selectbox("Select Project", list(project_options_edit_main_page.keys()), key="edit_proj_select_main_key", index=None, placeholder="Select a project...")
            
            if selected_proj_disp_edit_main_page:
                proj_id_to_edit_main_page = project_options_edit_main_page[selected_proj_disp_edit_main_page]
                proj_data_row = db.get_project_by_id(proj_id_to_edit_main_page) # Expects single row
                proj_data_main_page = dict(proj_data_row) if proj_data_row else None

                if proj_data_main_page:
                    # Main Project Details Form
                    with st.form(f"edit_project_form_main_page_{proj_id_to_edit_main_page}"):
                        st.markdown(f"#### Editing Project: {proj_data_main_page.get('ProjectName', '')} (ID: {proj_id_to_edit_main_page})")
                        pr_name_edit = st.text_input("Project Name*", value=proj_data_main_page.get('ProjectName',''))
                        
                        current_cust_id_proj_edit = proj_data_main_page.get('CustomerID')
                        project_customer_keys_list = list(customer_map_proj.keys())
                        try: 
                            proj_customer_index = project_customer_keys_list.index(next(k for k,v in customer_map_proj.items() if v == current_cust_id_proj_edit))
                        except (StopIteration, ValueError): 
                            proj_customer_index = 0 
                        selected_cust_name_proj_edit_page = st.selectbox("Customer*", project_customer_keys_list, index=proj_customer_index, key="edit_proj_customer_main_page")
                        pr_customer_id_edit = customer_map_proj.get(selected_cust_name_proj_edit_page)
                        
                        col_start_proj_edit, col_end_proj_edit = st.columns(2)
                        pr_start_date_val_edit = datetime.strptime(proj_data_main_page['StartDate'], "%Y-%m-%d").date() if proj_data_main_page.get('StartDate') else None
                        pr_end_date_val_edit = datetime.strptime(proj_data_main_page['EndDate'], "%Y-%m-%d").date() if proj_data_main_page.get('EndDate') else None
                        
                        pr_start_date_edit = col_start_proj_edit.date_input("Start Date", value=pr_start_date_val_edit)
                        pr_end_date_edit = col_end_proj_edit.date_input("Expected End Date", value=pr_end_date_val_edit)
                        
                        current_status = proj_data_main_page.get('Status')
                        pr_status_edit = st.selectbox("Status", project_status_options, 
                                                      index=project_status_options.index(current_status) if current_status in project_status_options else 0)
                        pr_budget_edit = st.number_input("Budget (Rs.)", value=float(proj_data_main_page.get('Budget',0.0)), min_value=0.0, format="%.2f")
                        pr_desc_edit = st.text_area("Description", value=proj_data_main_page.get('Description',''))
                        
                        submitted_update_project_details = st.form_submit_button("Update Project Core Details")
                        if submitted_update_project_details:
                            if not pr_name_edit: 
                                st.error("Project Name required.")
                            elif not pr_customer_id_edit: 
                                st.error("Customer is required for a project.")
                            else:
                                try:
                                    db.update_project(proj_id_to_edit_main_page, pr_name_edit, pr_customer_id_edit, 
                                                      pr_start_date_edit.strftime("%Y-%m-%d") if pr_start_date_edit else None, 
                                                      pr_end_date_edit.strftime("%Y-%m-%d") if pr_end_date_edit else None, 
                                                      pr_status_edit, pr_budget_edit, pr_desc_edit)
                                    st.success("Project core details updated!")
                                    st.rerun() # Rerun to reflect changes
                                except Exception as e_proj_edit: 
                                    st.error(f"Error updating project core details: {e_proj_edit}")
                    
                    st.markdown("---")
                    st.subheader("Project Materials")
                    project_materials_rows = db.get_materials_for_project(proj_id_to_edit_main_page)
                    project_materials_list = db.rows_to_dicts(project_materials_rows) if project_materials_rows else []

                    total_material_cost_for_project = 0
                    if project_materials_list:
                        df_proj_mats = pd.DataFrame(project_materials_list)
                        df_proj_mats['LineCost'] = df_proj_mats['QuantityUsed'] * df_proj_mats['CostPerUnitAtTimeOfUse']
                        total_material_cost_for_project = df_proj_mats['LineCost'].sum()
                        
                        cols_display_proj_mat = ['MaterialName', 'QuantityUsed', 'UnitOfMeasure', 'CostPerUnitAtTimeOfUse', 'LineCost']
                        # Add remove buttons
                        for index, row in df_proj_mats.iterrows():
                            col1, col2, col3, col4, col5, col_btn = st.columns([3,1,1,1,1,1])
                            col1.write(row['MaterialName'])
                            col2.write(f"{row['QuantityUsed']} {row['UnitOfMeasure']}")
                            col3.write(f"Rs. {row['CostPerUnitAtTimeOfUse']:.2f}")
                            col4.write(f"Rs. {row['LineCost']:.2f}")
                            # col5 can be for notes if you add them
                            if col_btn.button("Remove", key=f"remove_proj_mat_{row['ProjectMaterialID']}_{proj_id_to_edit_main_page}"):
                                try:
                                    db.remove_material_from_project(row['ProjectMaterialID']) # This should also handle stock adjustment
                                    st.success(f"Removed {row['MaterialName']} from project. Stock adjusted.")
                                    st.rerun()
                                except Exception as e_remove:
                                    st.error(f"Error removing material: {e_remove}")
                        st.markdown(f"**Total Material Cost for Project: Rs. {total_material_cost_for_project:,.2f}**")
                    else:
                        st.info("No materials assigned to this project yet.")

                    with st.expander("Add New Material to Project", expanded=False):
                        with st.form(f"add_material_to_project_form_{proj_id_to_edit_main_page}", clear_on_submit=True):
                            material_categories = db.get_distinct_material_categories() 
                            sel_cat_proj_mat = st.selectbox("Filter by Material Category", ["All"] + material_categories, key=f"cat_mat_proj_add_{proj_id_to_edit_main_page}")

                            if sel_cat_proj_mat and sel_cat_proj_mat != "All":
                                materials_options_rows = db.get_materials_by_category(sel_cat_proj_mat)
                            else:
                                materials_options_rows = db.get_all_materials()
                            
                            available_materials = db.rows_to_dicts(materials_options_rows) if materials_options_rows else []
                            
                            mat_map_proj_add = {"Select Material*": None}
                            for m in available_materials:
                                display_txt = f"{m.get('MaterialName','N/A')} (Stock: {m.get('QuantityInStock',0)} {m.get('UnitOfMeasure','')}; Cost: {m.get('CostPerUnit',0):.2f}; Supplier: {m.get('SupplierName','N/A')})"
                                mat_map_proj_add[display_txt] = m['MaterialID']
                            
                            selected_mat_disp_proj_add = st.selectbox("Select Specific Material*", list(mat_map_proj_add.keys()), key=f"sel_spec_mat_proj_add_{proj_id_to_edit_main_page}")
                            mat_id_to_add_proj_val = mat_map_proj_add.get(selected_mat_disp_proj_add)
                            
                            qty_needed_proj_add = st.number_input("Quantity Needed*", min_value=0.01, format="%.2f", step=0.1, key=f"qty_needed_proj_add_{proj_id_to_edit_main_page}")
                            notes_proj_mat_add = st.text_area("Notes (Optional)", key=f"notes_proj_mat_add_{proj_id_to_edit_main_page}")

                            submitted_add_material_to_proj = st.form_submit_button("➕ Add Material to Project")
                            if submitted_add_material_to_proj:
                                if mat_id_to_add_proj_val and qty_needed_proj_add > 0:
                                    mat_details_row = db.get_material_by_id(mat_id_to_add_proj_val) # Expects single row
                                    mat_details = dict(mat_details_row) if mat_details_row else None
                                    if mat_details:
                                        cost_at_time = mat_details.get('CostPerUnit', 0.0)
                                        current_stock = mat_details.get('QuantityInStock', 0.0)
                                        if qty_needed_proj_add > current_stock:
                                            st.warning(f"Needed quantity ({qty_needed_proj_add}) for {mat_details['MaterialName']} exceeds stock ({current_stock}). Proceeding will result in negative theoretical stock.")
                                        
                                        try:
                                            db.add_material_to_project(proj_id_to_edit_main_page, mat_id_to_add_proj_val, qty_needed_proj_add, cost_at_time, notes_proj_mat_add)
                                            db.update_material_stock(mat_id_to_add_proj_val, -qty_needed_proj_add) # Deduct stock
                                            st.success(f"Added {qty_needed_proj_add} of {mat_details['MaterialName']} to project. Stock updated.")
                                            st.rerun()
                                        except Exception as e: st.error(f"Error: {e}")
                                    else: st.error("Could not get material details.")
                                else: st.error("Material and Quantity Needed are required.")
                    
                    # Placeholder for Project Supplier Services (similar listing and adding could be done)
                    st.markdown("---")
                    st.subheader("Project Supplier Services")
                    project_services_rows = db.get_services_for_project(proj_id_to_edit_main_page)
                    project_services_list = db.rows_to_dicts(project_services_rows) if project_services_rows else []
                    if project_services_list:
                        st.dataframe(project_services_list, use_container_width=True, hide_index=True)
                    else:
                        st.info("No supplier services currently linked to this project.")
                    # TODO: Add UI to link existing or new supplier service to this project.

                else:
                    st.error(f"Could not load data for project ID {proj_id_to_edit_main_page}")

    elif action_proj == "Delete Project":
        # ... (Delete Project code as before) ...
        st.subheader("Delete Project")
        projects_list_del_rows = db.get_all_projects()
        if not projects_list_del_rows: 
            st.info("No projects to delete.")
        else:
            projects_list_del_main = db.rows_to_dicts(projects_list_del_rows)
            project_options_del_main_page = {f"{p.get('ProjectName','Unnamed Project')} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_list_del_main}
            selected_proj_disp_del_main_page = st.selectbox("Select Project to Delete", list(project_options_del_main_page.keys()), key="del_proj_select_main_key", index=None, placeholder="Select a project...")
            if selected_proj_disp_del_main_page:
                proj_id_to_del_main_page = project_options_del_main_page[selected_proj_disp_del_main_page]
                st.warning(f"Are you sure you want to delete project '{selected_proj_disp_del_main_page}'? This will also delete associated project materials and might affect orders, invoices, or expenses linked to it (depending on DB constraints).")
                if st.button("Confirm Delete Project", key=f"confirm_del_proj_main_page_{proj_id_to_del_main_page}"):
                    try:
                        db.delete_project(proj_id_to_del_main_page) # Ensure this cascades to ProjectMaterials or they are deleted first
                        st.success("Project deleted!")
                        st.rerun()
                    except Exception as e_del_proj_main: 
                        st.error(f"Error deleting project: {e_del_proj_main}")


elif choice == "Sales Book (Orders)":
    # ... (Sales Book code as before, ensure forms are robust) ...
    st.header("🛒 Sales Book (Orders)")
    action_order_main = st.selectbox("Action", ["View All Orders", "Create New Order", "Edit Order (Basic Info)"], key="order_action_main_key")
    
    if action_order_main == "View All Orders":
        st.subheader("Existing Orders")
        all_db_orders_rows = db.get_all_orders()
        if all_db_orders_rows:
            all_db_orders_main = db.rows_to_dicts(all_db_orders_rows)
            df_orders = pd.DataFrame(all_db_orders_main)
            if 'TotalAmount' in df_orders.columns:
                df_orders['TotalAmount_Display'] = df_orders['TotalAmount'].apply(lambda x: f"Rs. {x:,.2f}" if pd.notnull(x) else "N/A")
            
            cols_to_show = ['OrderID', 'OrderDate', 'CustomerName', 'ProjectName', 'ReferenceID', 'OrderStatus', 'TotalAmount_Display', 'PaymentStatus']
            cols_filtered = [col for col in cols_to_show if col in df_orders.columns]
            st.dataframe(df_orders[cols_filtered], use_container_width=True, hide_index=True)

            order_ids_for_view_main = [o['OrderID'] for o in all_db_orders_main] 
            if order_ids_for_view_main:
                selected_order_id_view_main = st.selectbox("Select Order ID to view items", order_ids_for_view_main, key="view_order_items_select_db_main_key", index=None, placeholder="Choose an order...")
                if selected_order_id_view_main:
                    items_for_order_rows = db.get_order_items_by_order_id(selected_order_id_view_main)
                    if items_for_order_rows:
                        st.write(f"Items for Order ID: {selected_order_id_view_main}")
                        st.dataframe(db.rows_to_dicts(items_for_order_rows), use_container_width=True, hide_index=True)
                    else: 
                        st.info("No items found for this order.")
        else: 
            st.info("No orders recorded yet.")

    elif action_order_main == "Create New Order":
        # ... (Create Order Form as before, ensuring product stock check is robust) ...
        st.subheader("Create New Order")
        customers_for_order_rows = db.get_all_customers()
        customers_for_order_main = db.rows_to_dicts(customers_for_order_rows) if customers_for_order_rows else []
        customer_map_order_main = {"Select Customer*": None}
        customer_map_order_main.update({f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_order_main})
        
        projects_for_order_rows = db.get_all_projects()
        projects_for_order_main = db.rows_to_dicts(projects_for_order_rows) if projects_for_order_rows else []
        project_map_order_main = {"None (No Project)": None}
        project_map_order_main.update({f"{p.get('ProjectName','Unnamed Project')} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_for_order_main})
        
        order_status_options_main = ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
        payment_status_options_main = ["Unpaid", "Partially Paid", "Paid", "Refunded"]
        
        with st.form("add_order_form_db_main_key", clear_on_submit=False): # clear_on_submit=False to keep item list
            o_order_date_main = st.date_input("Order Date", datetime.now().date())
            selected_cust_name_order_main = st.selectbox("Customer*", list(customer_map_order_main.keys()), key="order_cust_db_select_main_key", index=0)
            o_customer_id_main = customer_map_order_main.get(selected_cust_name_order_main)
            selected_proj_name_order_main = st.selectbox("Associated Project (Optional)", list(project_map_order_main.keys()), key="order_proj_db_select_main_key", index=0)
            o_project_id_main = project_map_order_main.get(selected_proj_name_order_main)

            o_reference_id_main = st.text_input("Order Reference ID (Optional, e.g., ORD-XYZ-001)") 

            col_ord_stat1_main, col_ord_stat2_main = st.columns(2)
            o_order_status_main = col_ord_stat1_main.selectbox("Order Status", order_status_options_main)
            o_payment_status_main = col_ord_stat2_main.selectbox("Payment Status", payment_status_options_main)
            
            initial_shipping_address_main = ""
            if o_customer_id_main:
                cust_details_row = db.get_customer_by_id(o_customer_id_main)
                cust_details_for_addr_main = dict(cust_details_row) if cust_details_row else None
                if cust_details_for_addr_main: 
                    initial_shipping_address_main = cust_details_for_addr_main.get('ShippingAddress') or cust_details_for_addr_main.get('BillingAddress', "")
            
            o_shipping_address_main = st.text_area("Shipping Address", value=initial_shipping_address_main, key="order_ship_addr_main_input_key_create") # Key used for potential state access
            o_notes_main = st.text_area("Order Notes")
            
            st.markdown("---"); st.subheader("Order Items")
            # st.session_state.current_order_items_main initialized globally
            
            products_for_items_rows = db.get_all_products()
            products_for_items_order_main = db.rows_to_dicts(products_for_items_rows) if products_for_items_rows else []
            product_map_order_items_main = {"Select Product*": None}
            product_map_order_items_main.update({f"{p['ProductName']} (ID: {p['ProductID']}, Price: Rs. {p.get('SellingPrice', 0.0):.2f}, Stock: {p.get('QuantityInStock',0)})": p['ProductID'] for p in products_for_items_order_main})
            
            item_cols_main = st.columns([3, 1, 1, 1, 0.5]) # Product, Qty, Price, Discount, AddBtn
            selected_prod_disp_item_main = item_cols_main[0].selectbox("Product*", list(product_map_order_items_main.keys()), key="order_item_prod_select_key_main_new", index=0)
            qty_item_main = item_cols_main[1].number_input("Qty*", min_value=1, value=1, step=1, key="order_item_qty_val_main_new")
            
            prod_id_for_price_main = product_map_order_items_main.get(selected_prod_disp_item_main)
            default_unit_price_main = 0.0
            if prod_id_for_price_main:
                prod_details_row = db.get_product_by_id(prod_id_for_price_main)
                prod_details_main = dict(prod_details_row) if prod_details_row else None
                if prod_details_main: 
                    default_unit_price_main = float(prod_details_main.get('SellingPrice', 0.0))
            
            unit_price_item_override_main = item_cols_main[2].number_input("Unit Price (Rs.)", min_value=0.0, value=default_unit_price_main, format="%.2f", key="order_item_price_val_main_new")
            discount_item_val_main = item_cols_main[3].number_input("Discount (Rs.)", min_value=0.0, value=0.0, format="%.2f", key="order_item_disc_val_main_new")
            
            if item_cols_main[4].button("➕ Add", key="order_add_item_button_key_main"):
                if prod_id_for_price_main and qty_item_main > 0:
                    prod_details_add_row = db.get_product_by_id(prod_id_for_price_main)
                    prod_details_add_main = dict(prod_details_add_row) if prod_details_add_row else None

                    if prod_details_add_main and prod_details_add_main.get('QuantityInStock', 0) < qty_item_main: 
                        st.warning(f"Not enough stock for {prod_details_add_main['ProductName']} (Available: {prod_details_add_main.get('QuantityInStock',0)}). Order item not added.")
                    elif prod_details_add_main:
                        st.session_state.current_order_items_main.append({
                            'ProductID': prod_id_for_price_main, 
                            'ProductName': prod_details_add_main.get('ProductName','N/A'), 
                            'QuantitySold': qty_item_main, 
                            'UnitPriceAtSale': unit_price_item_override_main, 
                            'Discount': discount_item_val_main, 
                            'LineTotal': (unit_price_item_override_main * qty_item_main) - discount_item_val_main
                        })
                        # No st.rerun() here, let form submission handle it or manage item list display explicitly
                    else:
                        st.error("Selected product details could not be fetched.")
                else: 
                    st.warning("Please select a product and enter a valid quantity.")
            
            if st.session_state.current_order_items_main:
                st.markdown("**Items in this Order:**")
                temp_items_df_main = pd.DataFrame(st.session_state.current_order_items_main)
                # Add remove button for items in session state
                # For now, just display:
                temp_items_df_main['UnitPriceAtSale_Display'] = temp_items_df_main['UnitPriceAtSale'].apply(lambda x: f"Rs. {x:,.2f}")
                temp_items_df_main['Discount_Display'] = temp_items_df_main['Discount'].apply(lambda x: f"Rs. {x:,.2f}")
                temp_items_df_main['LineTotal_Display'] = temp_items_df_main['LineTotal'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(temp_items_df_main[['ProductName', 'QuantitySold', 'UnitPriceAtSale_Display', 'Discount_Display', 'LineTotal_Display']], use_container_width=True, hide_index=True)
                current_total_amount_numeric_main = sum(item['LineTotal'] for item in st.session_state.current_order_items_main)
                st.metric("Calculated Order Total", f"Rs. {current_total_amount_numeric_main:,.2f}")
            
            submitted_order_db_main = st.form_submit_button("💾 Create Order")
            if submitted_order_db_main:
                if not o_customer_id_main: 
                    st.error("Customer is required.")
                elif not st.session_state.current_order_items_main: 
                    st.error("Order must have at least one item.")
                else:
                    final_shipping_address_main_val = st.session_state.get("order_ship_addr_main_input_key_create", initial_shipping_address_main) # Get value from widget state
                    try:
                        new_order_id_main = db.add_order(
                            o_order_date_main.strftime("%Y-%m-%d"), o_customer_id_main, o_project_id_main,
                            o_order_status_main, 0.0, o_payment_status_main, # TotalAmount will be updated
                            final_shipping_address_main_val, o_notes_main, o_reference_id_main
                        )
                        for item_data_main in st.session_state.current_order_items_main:
                            db.add_order_item(new_order_id_main, item_data_main['ProductID'], item_data_main['QuantitySold'], item_data_main['UnitPriceAtSale'], item_data_main['Discount'])
                            db.update_product_stock(item_data_main['ProductID'], -item_data_main['QuantitySold']) 
                        db.update_order_total(new_order_id_main) 
                        st.success(f"Order (ID: {new_order_id_main}) created successfully!")
                        st.session_state.current_order_items_main = [] 
                        st.rerun()
                    except Exception as e_ord_add: 
                        st.error(f"Error creating order: {e_ord_add}")

    elif action_order_main == "Edit Order (Basic Info)":
        # ... (Edit Order form as before) ...
        st.subheader("Edit Order (Basic Info)")
        all_orders_edit_rows = db.get_all_orders()
        if not all_orders_edit_rows:
            st.info("No orders to edit.")
        else:
            all_orders_edit = db.rows_to_dicts(all_orders_edit_rows)
            order_options_edit = {f"Order ID {o['OrderID']} (Ref: {o.get('ReferenceID', 'N/A')}, Cust: {o.get('CustomerName', 'N/A')})": o['OrderID'] for o in all_orders_edit}
            selected_order_key_edit = st.selectbox("Select Order to Edit", list(order_options_edit.keys()), key="edit_order_select", index=None, placeholder="Choose an order...")
            
            if selected_order_key_edit:
                order_id_to_edit = order_options_edit[selected_order_key_edit]
                order_data_row = db.get_order_by_id(order_id_to_edit) 
                order_data = dict(order_data_row) if order_data_row else None

                if order_data:
                    customers_for_order_edit_rows = db.get_all_customers()
                    customers_for_order_edit = db.rows_to_dicts(customers_for_order_edit_rows) if customers_for_order_edit_rows else []
                    customer_map_order_edit = {"Select Customer*": None}
                    customer_map_order_edit.update({f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_order_edit})
                    
                    projects_for_order_edit_rows = db.get_all_projects()
                    projects_for_order_edit = db.rows_to_dicts(projects_for_order_edit_rows) if projects_for_order_edit_rows else []
                    project_map_order_edit = {"None (No Project)": None}
                    project_map_order_edit.update({f"{p.get('ProjectName','Unnamed Project')} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_for_order_edit})

                    order_status_options_edit = ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
                    payment_status_options_edit = ["Unpaid", "Partially Paid", "Paid", "Refunded"]

                    with st.form(f"edit_order_form_{order_id_to_edit}"):
                        st.write(f"Editing Order ID: {order_id_to_edit}")
                        o_order_date_edit = st.date_input("Order Date", value=datetime.strptime(order_data.get('OrderDate',''), "%Y-%m-%d").date() if order_data.get('OrderDate') else datetime.now().date())
                        
                        cust_keys_edit = list(customer_map_order_edit.keys())
                        try:
                            cust_idx_edit = cust_keys_edit.index(next((k for k, v in customer_map_order_edit.items() if v == order_data.get('CustomerID')), cust_keys_edit[0]))
                        except (StopIteration, ValueError): cust_idx_edit = 0
                        selected_cust_name_edit = st.selectbox("Customer*", cust_keys_edit, index=cust_idx_edit, key=f"order_cust_edit_{order_id_to_edit}")
                        o_customer_id_edit = customer_map_order_edit.get(selected_cust_name_edit)

                        proj_keys_edit = list(project_map_order_edit.keys())
                        try:
                            proj_idx_edit = proj_keys_edit.index(next((k for k, v in project_map_order_edit.items() if v == order_data.get('ProjectID')), proj_keys_edit[0]))
                        except (StopIteration, ValueError): proj_idx_edit = 0
                        selected_proj_name_edit = st.selectbox("Associated Project (Optional)", proj_keys_edit, index=proj_idx_edit, key=f"order_proj_edit_{order_id_to_edit}")
                        o_project_id_edit = project_map_order_edit.get(selected_proj_name_edit)

                        o_reference_id_edit = st.text_input("Order Reference ID", value=order_data.get('ReferenceID', ''))

                        col_ord_stat1_edit, col_ord_stat2_edit = st.columns(2)
                        current_order_status = order_data.get('OrderStatus')
                        order_status_idx = order_status_options_edit.index(current_order_status) if current_order_status in order_status_options_edit else 0
                        o_order_status_edit = col_ord_stat1_edit.selectbox("Order Status", order_status_options_edit, index=order_status_idx)
                        
                        current_payment_status = order_data.get('PaymentStatus')
                        payment_status_idx = payment_status_options_edit.index(current_payment_status) if current_payment_status in payment_status_options_edit else 0
                        o_payment_status_edit = col_ord_stat2_edit.selectbox("Payment Status", payment_status_options_edit, index=payment_status_idx)
                        
                        o_shipping_address_edit = st.text_area("Shipping Address", value=order_data.get('ShippingAddress', ''))
                        o_notes_edit = st.text_area("Order Notes", value=order_data.get('Notes', ''))
                        st.text_input("Total Amount (Calculated)", value=f"Rs. {order_data.get('TotalAmount', 0.0):,.2f}", disabled=True)

                        submitted_edit_order = st.form_submit_button("💾 Update Order Info")
                        if submitted_edit_order:
                            if not o_customer_id_edit:
                                st.error("Customer is required.")
                            else:
                                try:
                                    db.update_order_basic_info(
                                        order_id_to_edit, o_order_date_edit.strftime("%Y-%m-%d"), o_customer_id_edit,
                                        o_project_id_edit, o_order_status_edit, o_payment_status_edit,
                                        o_shipping_address_edit, o_notes_edit, o_reference_id_edit
                                    )
                                    # Note: db.update_order_total(order_id_to_edit) might be needed if anything affecting total changed.
                                    st.success(f"Order (ID: {order_id_to_edit}) basic info updated!")
                                    st.rerun()
                                except Exception as e_ord_edit:
                                    st.error(f"Error updating order: {e_ord_edit}")
                else:
                    st.error(f"Could not fetch order data for ID {order_id_to_edit}.")


elif choice == "Invoice Tracking":
    st.header("🧾 Invoice Tracking")
    action_inv = st.selectbox("Action", ["View All Invoices", "Create New Invoice", "Edit Invoice"], key="inv_action")
    invoice_status_options = ["Draft", "Sent", "Paid", "Overdue", "Cancelled"]
    
    all_projects_inv_rows = db.get_all_projects() 
    all_projects_inv = db.rows_to_dicts(all_projects_inv_rows) if all_projects_inv_rows else []
    project_map_inv = {"Select Project*": None}
    project_map_inv.update({f"{p.get('ProjectName','Unnamed Project')} (ID: {p['ProjectID']}, Cust: {p.get('CustomerName', 'N/A')})": p['ProjectID'] for p in all_projects_inv})

    if action_inv == "View All Invoices":
        # ... (View Invoices code, using hide_index=True for dataframes) ...
        st.subheader("All Invoices")
        search_term_inv = st.text_input("Search Invoices (Ref ID, Project, Customer)", key="search_inv_view")
        invoices_list_rows = db.get_all_invoices(search_term=search_term_inv) 
        if invoices_list_rows:
            invoices_list = db.rows_to_dicts(invoices_list_rows)
            df_invoices = pd.DataFrame(invoices_list)
            df_invoices['TotalAmount_Display'] = df_invoices['TotalAmount'].apply(lambda x: f"Rs. {x:,.2f}" if pd.notnull(x) else "N/A")
            df_invoices['IssueDate_Display'] = pd.to_datetime(df_invoices['IssueDate'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('N/A')
            df_invoices['DueDate_Display'] = pd.to_datetime(df_invoices['DueDate'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('N/A')
            
            if 'PaymentDate' in df_invoices.columns:
                df_invoices['PaymentDate_Display'] = pd.to_datetime(df_invoices['PaymentDate'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('N/A')
            else:
                df_invoices['PaymentDate_Display'] = 'N/A'

            cols_to_show = ['InvoiceID', 'InvoiceReferenceID', 'ProjectName', 'CustomerName', 'TotalAmount_Display', 'Status', 'IssueDate_Display', 'DueDate_Display', 'PaymentDate_Display', 'Notes']
            cols_filtered = [col for col in cols_to_show if col in df_invoices.columns]
            st.dataframe(df_invoices[cols_filtered], use_container_width=True, hide_index=True)
        else:
            st.info("No invoices found.")

    elif action_inv == "Create New Invoice":
        st.subheader("Create New Invoice for Project")
        with st.form("add_invoice_form", clear_on_submit=True):
            selected_project_key_inv = st.selectbox("Select Project to Invoice*", list(project_map_inv.keys()), key="inv_project_select", index=0)
            inv_project_id = project_map_inv.get(selected_project_key_inv)

            inv_ref_id_default = db.get_next_invoice_reference_id() if hasattr(db, 'get_next_invoice_reference_id') else f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            inv_ref_id = st.text_input("Invoice Reference ID*", value=inv_ref_id_default)

            inv_issue_date = st.date_input("Issue Date*", datetime.now().date())
            inv_due_date = st.date_input("Due Date*", datetime.now().date() + timedelta(days=30))
            
            customer_id_for_inv = None
            project_budget_for_inv = 0.0 
            customer_name_display = "N/A"
            if inv_project_id:
                project_data_row = db.get_project_by_id(inv_project_id)
                project_data_inv = dict(project_data_row) if project_data_row else None
                if project_data_inv:
                    customer_id_for_inv = project_data_inv.get('CustomerID')
                    project_budget_for_inv = float(project_data_inv.get('Budget', 0.0)) 
                    if customer_id_for_inv:
                        customer_details_row = db.get_customer_by_id(customer_id_for_inv)
                        customer_details_inv = dict(customer_details_row) if customer_details_row else None
                        if customer_details_inv:
                            customer_name_display = customer_details_inv.get('CustomerName', 'N/A')
            
            st.text_input("Customer (Auto-filled from Project)", value=customer_name_display, disabled=True)
            inv_amount_default_value = max(project_budget_for_inv, 0.01) # Fix for StreamlitValueBelowMinError
            inv_amount = st.number_input("Invoice Amount (Rs.)*", value=inv_amount_default_value, min_value=0.01, format="%.2f")
            inv_status = st.selectbox("Status*", invoice_status_options, index=invoice_status_options.index("Draft") if "Draft" in invoice_status_options else 0)
            inv_payment_date = st.date_input("Payment Date (if Paid)", value=None) 
            inv_notes = st.text_area("Notes / Invoice Line Items (Manual Entry)")

            submitted = st.form_submit_button("Create Invoice")
            if submitted:
                if not inv_project_id or not inv_ref_id or not customer_id_for_inv:
                    st.error("Project (which determines Customer) and Invoice Reference ID are required.")
                else:
                    try:
                        db.add_invoice(
                            inv_ref_id, inv_project_id, customer_id_for_inv,
                            inv_issue_date.strftime("%Y-%m-%d"), 
                            inv_due_date.strftime("%Y-%m-%d"),
                            inv_payment_date.strftime("%Y-%m-%d") if inv_payment_date else None,
                            inv_amount, inv_status, inv_notes
                        )
                        st.success(f"Invoice {inv_ref_id} created successfully!")
                    except Exception as e:
                        st.error(f"Error creating invoice: {e}")
    
    elif action_inv == "Edit Invoice":
        # ... (Edit Invoice code, similar fix for inv_amount_edit as in create) ...
        st.subheader("Edit Invoice")
        invoices_list_edit_rows = db.get_all_invoices() 
        if not invoices_list_edit_rows:
            st.info("No invoices to edit.")
        else:
            invoices_list_edit = db.rows_to_dicts(invoices_list_edit_rows)
            invoice_options_edit = {f"{inv.get('InvoiceReferenceID','N/A')} (Project: {inv.get('ProjectName', 'N/A')}, ID: {inv['InvoiceID']})": inv['InvoiceID'] for inv in invoices_list_edit}
            selected_invoice_key_edit = st.selectbox("Select Invoice to Edit", list(invoice_options_edit.keys()), key="edit_invoice_select", index=None, placeholder="Choose an invoice...")

            if selected_invoice_key_edit:
                invoice_id_to_edit = invoice_options_edit[selected_invoice_key_edit]
                invoice_data_row = db.get_invoice_by_id(invoice_id_to_edit) 
                invoice_data = dict(invoice_data_row) if invoice_data_row else None

                if invoice_data:
                    with st.form(f"edit_invoice_form_{invoice_id_to_edit}"):
                        st.write(f"Editing Invoice: {invoice_data.get('InvoiceReferenceID','N/A')}")
                        inv_ref_id_edit = st.text_input("Invoice Reference ID*", value=invoice_data.get('InvoiceReferenceID',''))
                        
                        project_name_display = "N/A"
                        if invoice_data.get('ProjectID'):
                            project_details_row = db.get_project_by_id(invoice_data['ProjectID'])
                            project_details_for_edit = dict(project_details_row) if project_details_row else None
                            if project_details_for_edit: project_name_display = project_details_for_edit.get('ProjectName', 'N/A')
                        st.text_input("Project", value=project_name_display, disabled=True)
                        
                        customer_name_display_edit = "N/A"
                        if invoice_data.get('CustomerID'):
                            customer_details_row = db.get_customer_by_id(invoice_data['CustomerID'])
                            customer_details_for_edit = dict(customer_details_row) if customer_details_row else None
                            if customer_details_for_edit: customer_name_display_edit = customer_details_for_edit.get('CustomerName', 'N/A')
                        st.text_input("Customer", value=customer_name_display_edit, disabled=True)

                        inv_issue_date_edit = st.date_input("Issue Date*", value=datetime.strptime(invoice_data['IssueDate'], "%Y-%m-%d").date() if invoice_data.get('IssueDate') else datetime.now().date())
                        inv_due_date_edit = st.date_input("Due Date*", value=datetime.strptime(invoice_data['DueDate'], "%Y-%m-%d").date() if invoice_data.get('DueDate') else datetime.now().date() + timedelta(days=30))
                        
                        inv_amount_edit_default_value = max(float(invoice_data.get('TotalAmount',0.0)), 0.01) # Fix
                        inv_amount_edit = st.number_input("Invoice Amount (Rs.)*", value=inv_amount_edit_default_value, min_value=0.01, format="%.2f")
                        
                        current_inv_status = invoice_data.get('Status')
                        current_status_index = invoice_status_options.index(current_inv_status) if current_inv_status in invoice_status_options else 0
                        inv_status_edit = st.selectbox("Status*", invoice_status_options, index=current_status_index)
                        
                        inv_payment_date_val_edit = datetime.strptime(invoice_data['PaymentDate'], "%Y-%m-%d").date() if invoice_data.get('PaymentDate') else None
                        inv_payment_date_edit = st.date_input("Payment Date (if Paid)", value=inv_payment_date_val_edit)
                        
                        inv_notes_edit = st.text_area("Notes / Invoice Line Items", value=invoice_data.get('Notes', ''))

                        updated = st.form_submit_button("Update Invoice")
                        if updated:
                            if not inv_ref_id_edit:
                                st.error("Invoice Reference ID is required.")
                            else:
                                try:
                                    db.update_invoice(
                                        invoice_id_to_edit, inv_ref_id_edit,
                                        invoice_data['ProjectID'], invoice_data['CustomerID'], 
                                        inv_issue_date_edit.strftime("%Y-%m-%d"),
                                        inv_due_date_edit.strftime("%Y-%m-%d"),
                                        inv_payment_date_edit.strftime("%Y-%m-%d") if inv_payment_date_edit else None,
                                        inv_amount_edit, inv_status_edit, inv_notes_edit
                                    )
                                    st.success(f"Invoice {inv_ref_id_edit} updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating invoice: {e}")
                else:
                    st.error(f"Could not load invoice data for ID {invoice_id_to_edit}.")

elif choice == "Expense Tracking":
    # ... (Expense Tracking code as before) ...
    st.header("💸 Expense Tracking")
    projects_for_exp_rows = db.get_all_projects()
    projects_for_exp_main = db.rows_to_dicts(projects_for_exp_rows) if projects_for_exp_rows else []
    project_map_exp_main_scope = {"None (No Project)": None}
    project_map_exp_main_scope.update({f"{p.get('ProjectName','Unnamed Project')} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_for_exp_main})
    
    action_exp_main_page = st.selectbox("Action", ["View All", "Add New (Manual)"], key="exp_action_main_page_key")
    if action_exp_main_page == "View All":
        st.subheader("Recorded Expenses")
        all_db_expenses_rows = db.get_all_expenses() 
        if all_db_expenses_rows:
            all_db_expenses_main_page = db.rows_to_dicts(all_db_expenses_rows)
            df_expenses_main_page = pd.DataFrame(all_db_expenses_main_page)
            if 'Amount' in df_expenses_main_page.columns: 
                df_expenses_main_page['Amount_Display'] = df_expenses_main_page['Amount'].apply(lambda x: f"Rs. {x:,.2f}" if pd.notnull(x) else "N/A")
            
            cols_exp_disp_main = ['ExpenseID', 'ExpenseDate', 'Description', 'Category', 'Amount_Display', 'Vendor', 'ProjectName', 'ReceiptReference', 'SupplierServiceName'] 
            cols_exp_disp_filt_main = [col for col in cols_exp_disp_main if col in df_expenses_main_page.columns]
            st.dataframe(df_expenses_main_page[cols_exp_disp_filt_main], use_container_width=True, hide_index=True)
        else: 
            st.info("No expenses recorded yet.")
    elif action_exp_main_page == "Add New (Manual)":
        st.subheader("Add New Manual Expense")
        with st.form("add_manual_expense_form_db_main_key", clear_on_submit=True):
            exp_date_man_main = st.date_input("Expense Date", datetime.now().date())
            desc_exp_man_main = st.text_input("Description*")
            cat_exp_opts_man_main = ["Operational", "Marketing", "COGS", "Salaries", "Utilities", "Rent", "Travel", "Manual Adjustment", "Other"]
            cat_exp_man_main = st.selectbox("Category", cat_exp_opts_man_main)
            amt_exp_man_main = st.number_input("Amount (Rs.)*", min_value=0.01, format="%.2f")
            vendor_exp_man_main = st.text_input("Vendor/Payee")
            selected_proj_name_exp_man_main = st.selectbox("Associated Project (Optional)", list(project_map_exp_main_scope.keys()), key="exp_manual_proj_db_select_main_key", index=0)
            exp_project_id_man_main = project_map_exp_main_scope.get(selected_proj_name_exp_man_main)
            receipt_ref_exp_man_main = st.text_input("Receipt Reference (e.g., bill number, path to scanned receipt)")
            submitted_exp_man_main = st.form_submit_button("Add Manual Expense")
            if submitted_exp_man_main:
                if not desc_exp_man_main or amt_exp_man_main <= 0: 
                    st.error("Description and a valid Amount are required.")
                else:
                    try:
                        db.add_expense(exp_date_man_main.strftime("%Y-%m-%d"), desc_exp_man_main, cat_exp_man_main, amt_exp_man_main, vendor_exp_man_main, exp_project_id_man_main, receipt_ref_exp_man_main, None) 
                        st.success("Manual expense added successfully!")
                    except Exception as e_exp_add: 
                        st.error(f"Error adding manual expense: {e_exp_add}")

elif choice == "Reports":
    # ... (Reports code as before) ...
    st.header("📈 Reports")
    st.info("Reporting section provides basic summaries. More detailed visualizations and queries can be added.")
    report_type_main = st.selectbox("Select Report Type (Basic Examples)", 
                                    ["Overall Financial Summary", "Project Profitability (Simplified)", 
                                     "Sales by Product (Placeholder)", "Inventory Status (Placeholder)"])
    if report_type_main == "Overall Financial Summary":
        all_invoices_rep_rows = db.get_all_invoices()
        all_invoices_rep = db.rows_to_dicts(all_invoices_rep_rows) if all_invoices_rep_rows else []
        
        expenses_main_rep_rows = db.get_all_expenses()
        expenses_main_rep = db.rows_to_dicts(expenses_main_rep_rows) if expenses_main_rep_rows else []

        total_revenue_from_paid_invoices_rep = sum(inv['TotalAmount'] for inv in all_invoices_rep if inv.get('Status') == 'Paid' and inv.get('TotalAmount'))
        total_operational_expenses_main_rep = sum(e['Amount'] for e in expenses_main_rep if e.get('Amount') and e.get('Category') != 'COGS')
        total_cogs_expenses_rep = sum(e['Amount'] for e in expenses_main_rep if e.get('Amount') and e.get('Category') == 'COGS')


        st.metric("Total Revenue (from Paid Invoices)", f"Rs. {total_revenue_from_paid_invoices_rep:,.2f}")
        st.metric("Total Cost of Goods Sold (COGS)", f"Rs. {total_cogs_expenses_rep:,.2f}")
        gross_profit = total_revenue_from_paid_invoices_rep - total_cogs_expenses_rep
        st.metric("Gross Profit", f"Rs. {gross_profit:,.2f}")
        st.metric("Total Operational Expenses (excl. COGS)", f"Rs. {total_operational_expenses_main_rep:,.2f}")
        net_operating_income = gross_profit - total_operational_expenses_main_rep
        st.metric("Net Operating Income", f"Rs. {net_operating_income:,.2f}")
        st.caption("Note: This summary relies on accurate 'Paid' invoice statuses and categorized expenses (especially 'COGS'). Supplier service costs are included if logged as expenses.")

    elif report_type_main == "Project Profitability (Simplified)":
        st.subheader("Project Profitability (Simplified)")
        projects_rep_rows = db.get_all_projects()
        if projects_rep_rows:
            projects_rep = db.rows_to_dicts(projects_rep_rows)
            report_data = []
            for proj in projects_rep:
                proj_id = proj['ProjectID']
                project_name = proj.get('ProjectName', f"Project ID {proj_id}")
                
                invoices_for_proj_rows = db.get_invoices_by_project_id(proj_id) 
                invoices_for_proj = db.rows_to_dicts(invoices_for_proj_rows) if invoices_for_proj_rows else []
                revenue_for_proj = sum(inv['TotalAmount'] for inv in invoices_for_proj if inv.get('Status') == 'Paid' and inv.get('TotalAmount'))
                
                # Costs for project: manual expenses + supplier services linked + project materials cost
                total_project_cost = 0
                
                # Manual expenses linked to project
                manual_expenses_for_proj_rows = db.get_expenses_by_project_id(proj_id) 
                manual_expenses_for_proj = db.rows_to_dicts(manual_expenses_for_proj_rows) if manual_expenses_for_proj_rows else []
                total_project_cost += sum(exp['Amount'] for exp in manual_expenses_for_proj if exp.get('Amount'))

                # Supplier services linked to project (if not already covered by auto-logged expenses)
                # This might double count if supplier services auto-log to Expenses table AND are also linked to project.
                # For simplicity, let's assume they are distinct or db.get_expenses_by_project_id filters out auto-logged service expenses.
                # A better approach is to ensure supplier services costs are consistently logged as 'Expenses' with category 'COGS' or 'Service Costs'.
                # For now, let's sum supplier service costs linked to project directly.
                services_for_proj_rows = db.get_services_for_project(proj_id)
                services_for_proj = db.rows_to_dicts(services_for_proj_rows) if services_for_proj_rows else []
                total_project_cost += sum(serv.get('Cost', 0.0) for serv in services_for_proj if not serv.get('IsExpenseLogged')) # Add only if not already logged as an expense

                # Project Materials cost
                project_mats_rows = db.get_materials_for_project(proj_id)
                project_mats = db.rows_to_dicts(project_mats_rows) if project_mats_rows else []
                total_project_cost += sum(pm.get('QuantityUsed',0) * pm.get('CostPerUnitAtTimeOfUse',0) for pm in project_mats)

                profit_for_proj = revenue_for_proj - total_project_cost
                report_data.append({
                    "Project Name": project_name,
                    "Total Revenue (Paid Invoices)": revenue_for_proj,
                    "Total Estimated Costs": total_project_cost,
                    "Estimated Profit/Loss": profit_for_proj
                })
            
            if report_data:
                df_report = pd.DataFrame(report_data)
                df_report["Total Revenue (Paid Invoices)"] = df_report["Total Revenue (Paid Invoices)"].apply(lambda x: f"Rs. {x:,.2f}")
                df_report["Total Estimated Costs"] = df_report["Total Estimated Costs"].apply(lambda x: f"Rs. {x:,.2f}")
                df_report["Estimated Profit/Loss"] = df_report["Estimated Profit/Loss"].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(df_report, use_container_width=True, hide_index=True)
            else:
                st.info("No project data with financial transactions to report on.")
        else:
            st.info("No projects available for reporting.")
    
    elif report_type_main == "Sales by Product (Placeholder)":
        st.info("This report is a placeholder and needs implementation (e.g., querying OrderItems and Products).")

    elif report_type_main == "Inventory Status (Placeholder)":
        st.info("This report is a placeholder and needs implementation (e.g., querying Products for stock levels, reorder points).")


st.sidebar.markdown("---")
st.sidebar.info("BACHAT-Management System")
