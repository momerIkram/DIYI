import streamlit as st
import pandas as pd
from datetime import datetime
import os
import database as db # Your database module
from PIL import Image

st.set_page_config(layout="wide")
st.title("🛋️ Furniture Startup Management System (v0.5 - Supplier Services)")

# --- Helper for saving uploaded file (modified for receipts) ---
def save_uploaded_receipt(uploaded_file, service_id): # Changed parameters
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        # Ensure RECEIPT_DIR exists when saving
        if not os.path.exists(db.RECEIPT_DIR): 
            os.makedirs(db.RECEIPT_DIR)

        filename = f"service_{service_id}_receipt{file_extension}"
        receipt_path = os.path.join(db.RECEIPT_DIR, filename)
        
        with open(receipt_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return receipt_path
    return None

# Helper for product images (remains similar)
def save_uploaded_product_image(uploaded_file, product_id_or_sku): # Renamed for clarity
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        # Ensure IMAGE_DIR exists
        if not os.path.exists(db.IMAGE_DIR):
            os.makedirs(db.IMAGE_DIR)
        filename = f"product_{product_id_or_sku}{file_extension}" # Use SKU if ID not yet available for new product
        img_path = os.path.join(db.IMAGE_DIR, filename)
        with open(img_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return img_path
    return None

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
modules = [
    "Dashboard", "Customer Management", "Supplier Management",
    "Supplier Services", # New Module
    "Material Management", "Product Management", "Project Management",
    "Sales Book (Orders)", "Expense Tracking", "Reports"
]
choice = st.sidebar.radio("Go to", modules)

# --- Module Implementations ---

if choice == "Dashboard":
    st.header("📊 Dashboard")
    customers = db.get_all_customers()
    products = db.get_all_products()
    suppliers = db.get_all_suppliers()
    materials = db.get_all_materials()
    projects = db.get_all_projects()
    orders = db.get_all_orders()
    expenses = db.get_all_expenses()
    services_count = len(db.get_all_supplier_services())


    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Customers", len(customers))
    col2.metric("Total Products", len(products))
    col3.metric("Total Suppliers", len(suppliers))
    col4.metric("Total Materials", len(materials))
    
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Total Projects", len(projects))
    
    total_revenue = sum(o['TotalAmount'] for o in orders if o['TotalAmount']) if orders else 0
    col6.metric("Total Sales Revenue", f"Rs. {total_revenue:,.2f}")
    
    total_expenses_val = sum(e['Amount'] for e in expenses if e['Amount']) if expenses else 0
    col7.metric("Total Expenses", f"Rs. {total_expenses_val:,.2f}")
    col8.metric("Total Supplier Services Logged", services_count)
    
    st.subheader("Recent Orders")
    if orders:
        st.dataframe(db.rows_to_dicts(orders[:5]), use_container_width=True)
    else:
        st.info("No orders yet.")

elif choice == "Customer Management":
    st.header("👥 Customer Management")
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
    
    elif action == "Edit Customer":
        st.subheader("Edit Customer")
        customers_list_edit = db.get_all_customers()
        if not customers_list_edit: st.info("No customers to edit.")
        else:
            customer_options_edit = {f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_list_edit}
            selected_cust_disp_edit = st.selectbox("Select Customer to Edit", list(customer_options_edit.keys()), key="edit_cust_select_page") # Unique key
            if selected_cust_disp_edit:
                cust_id_to_edit = customer_options_edit[selected_cust_disp_edit]
                cust_data_edit = db.get_customer_by_id(cust_id_to_edit)
                if cust_data_edit:
                    with st.form(f"edit_customer_form_page_{cust_id_to_edit}"): # Unique key for form
                        name = st.text_input("Customer Name*", value=cust_data_edit['CustomerName'])
                        email = st.text_input("Email", value=cust_data_edit['Email'])
                        phone = st.text_input("Phone", value=cust_data_edit['Phone'])
                        bill_addr = st.text_area("Billing Address", value=cust_data_edit['BillingAddress'])
                        ship_addr = st.text_area("Shipping Address", value=cust_data_edit['ShippingAddress'])
                        notes = st.text_area("Notes", value=cust_data_edit['Notes'])
                        updated = st.form_submit_button("Update Customer")
                        if updated:
                            if not name: st.error("Customer name is required.")
                            else:
                                try:
                                    db.update_customer(cust_id_to_edit, name, email, phone, bill_addr, ship_addr, notes)
                                    st.success("Customer updated successfully!")
                                    st.experimental_rerun()
                                except Exception as e: st.error(f"Error: {e}")
    elif action == "Delete Customer":
        st.subheader("Delete Customer")
        customers_list_del = db.get_all_customers()
        if not customers_list_del: st.info("No customers to delete.")
        else:
            customer_options_del = {f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_list_del}
            selected_cust_disp_del = st.selectbox("Select Customer to Delete", list(customer_options_del.keys()), key="del_cust_select_page") # Unique key
            if selected_cust_disp_del:
                cust_id_to_del = customer_options_del[selected_cust_disp_del]
                st.warning(f"Are you sure you want to delete {selected_cust_disp_del}? This might fail if the customer has associated records (orders, projects).")
                if st.button("Confirm Delete", key=f"confirm_del_cust_page_{cust_id_to_del}"): # Unique key
                    try:
                        db.delete_customer(cust_id_to_del)
                        st.success(f"Customer {selected_cust_disp_del} deleted successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error deleting customer: {e}")


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
        suppliers_list_del = db.get_all_suppliers()
        if not suppliers_list_del: st.info("No suppliers to delete.")
        else:
            supplier_options_del = {f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_list_del}
            selected_sup_disp_del = st.selectbox("Select Supplier to Delete", list(supplier_options_del.keys()), key="del_sup_select")
            if selected_sup_disp_del:
                sup_id_to_del = supplier_options_del[selected_sup_disp_del]
                st.warning(f"Are you sure you want to delete {selected_sup_disp_del}? This may affect product/material/service records by setting their supplier to 'None'.")
                if st.button("Confirm Delete", key=f"confirm_del_sup_{sup_id_to_del}"):
                    try:
                        db.delete_supplier(sup_id_to_del)
                        st.success(f"Supplier {selected_sup_disp_del} deleted!")
                        st.experimental_rerun()
                    except Exception as e: st.error(f"Error deleting supplier: {e}")

elif choice == "Supplier Services":
    st.header("🛠️ Supplier Services Management")
    action_ss = st.selectbox("Action", ["View All Services", "Add New Service", "Edit Service", "Delete Service"], key="ss_action")

    all_suppliers_ss = db.get_all_suppliers()
    supplier_map_ss = {"Select Supplier*": None}
    supplier_map_ss.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in all_suppliers_ss})

    all_projects_ss = db.get_all_projects()
    project_map_ss = {"None (General Service)": None}
    project_map_ss.update({f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in all_projects_ss})
    
    service_type_options = ["Paint Work", "Wood Cutting", "Polishing", "Stitching", "Assembly", "Transportation", "Consultation", "Other"]

    if action_ss == "View All Services":
        st.subheader("Recorded Supplier Services")
        search_term_ss = st.text_input("Search Services (Name, Type, Supplier, Project, Desc.)", key="search_ss_view")
        services_list = db.get_all_supplier_services(search_term=search_term_ss)
        if services_list:
            df_services = pd.DataFrame(db.rows_to_dicts(services_list))
            if 'Cost' in df_services.columns:
                 df_services['Cost_Display'] = df_services['Cost'].apply(lambda x: f"Rs. {x:,.2f}")
            
            cols_to_show = ['ServiceID', 'ServiceName', 'ServiceType', 'SupplierName', 'ProjectName', 
                            'ServiceDate', 'Cost_Display', 'Description', 'IsExpenseLogged']
            cols_to_show_filtered = [col for col in cols_to_show if col in df_services.columns]
            st.dataframe(df_services[cols_to_show_filtered], use_container_width=True)

            for service_row_dict in db.rows_to_dicts(services_list):
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
            selected_supplier_name_ss = st.selectbox("Supplier*", list(supplier_map_ss.keys()), key="add_ss_supplier")
            ss_supplier_id = supplier_map_ss.get(selected_supplier_name_ss)

            selected_project_name_ss = st.selectbox("Associated Project (Optional)", list(project_map_ss.keys()), key="add_ss_project")
            ss_project_id = project_map_ss.get(selected_project_name_ss)
            
            ss_service_name = st.text_input("Service Name/Title*", help="e.g., Custom painting for chair X, Polishing dining table set")
            ss_service_type_selected = st.selectbox("Service Type*", service_type_options, key="add_ss_type")
            ss_service_type_final = ss_service_type_selected
            if ss_service_type_selected == "Other":
                ss_service_type_other = st.text_input("Specify Other Service Type", key="add_ss_type_other")
                if ss_service_type_other: ss_service_type_final = ss_service_type_other


            ss_service_date = st.date_input("Service Date*", datetime.now().date())
            ss_cost = st.number_input("Service Cost (Rs.)*", min_value=0.0, format="%.2f")
            ss_receipt_upload = st.file_uploader("Upload Receipt (Optional)", type=['png', 'jpg', 'jpeg', 'pdf'])
            ss_description = st.text_area("Description/Notes")

            submitted = st.form_submit_button("Add Service")
            if submitted:
                if not ss_supplier_id or not ss_service_name or not ss_service_type_final or ss_cost < 0: # Check final type
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
                                db.update_supplier_service(new_service_id, ss_supplier_id, ss_project_id,
                                                           ss_service_name, ss_service_type_final, 
                                                           ss_service_date.strftime("%Y-%m-%d"), ss_cost,
                                                           receipt_file_path, ss_description) # Update with receipt path
                                st.success(f"Service (ID: {new_service_id}) added with receipt!")
                            else:
                                st.warning(f"Service (ID: {new_service_id}) added, but receipt upload failed.")
                        elif new_service_id:
                             st.success(f"Service (ID: {new_service_id}) added!")
                        
                        if expense_auto_logged:
                            st.info("This service cost has been automatically logged as an expense.")
                        elif new_service_id and ss_cost > 0:
                            st.warning("Service added, but automatic expense logging might have an issue. Please verify expenses.")
                            
                    except Exception as e:
                        st.error(f"Error adding service: {e}")
    
    elif action_ss == "Edit Service":
        st.subheader("Edit Supplier Service")
        services_list_edit = db.get_all_supplier_services()
        if not services_list_edit: st.info("No services to edit.")
        else:
            service_options = {f"{s['ServiceName']} by {s['SupplierName']} (ID: {s['ServiceID']})": s['ServiceID'] for s in services_list_edit}
            selected_service_disp = st.selectbox("Select Service to Edit", list(service_options.keys()), key="edit_ss_select")

            if selected_service_disp:
                service_id_to_edit = service_options[selected_service_disp]
                service_data = db.get_supplier_service_by_id(service_id_to_edit)
                if service_data:
                    with st.form(f"edit_supplier_service_form_{service_id_to_edit}"):
                        st.write(f"Editing Service ID: {service_data['ServiceID']}")

                        current_supplier_id_ss = service_data['SupplierID']
                        current_supplier_key_ss = "Select Supplier*"
                        supplier_keys_list = list(supplier_map_ss.keys())
                        try:
                            supplier_index = supplier_keys_list.index(next(k for k,v in supplier_map_ss.items() if v == current_supplier_id_ss))
                        except StopIteration: supplier_index = 0 # Default if not found
                        selected_supplier_name_ss_edit = st.selectbox("Supplier*", supplier_keys_list, index=supplier_index, key=f"edit_ss_supplier_{service_id_to_edit}")
                        ss_supplier_id = supplier_map_ss.get(selected_supplier_name_ss_edit)

                        current_project_id_ss = service_data['ProjectID']
                        current_project_key_ss = "None (General Service)"
                        project_keys_list = list(project_map_ss.keys())
                        try:
                            project_index = project_keys_list.index(next(k for k,v in project_map_ss.items() if v == current_project_id_ss))
                        except StopIteration: project_index = 0
                        selected_project_name_ss_edit = st.selectbox("Associated Project (Optional)", project_keys_list, index=project_index, key=f"edit_ss_project_{service_id_to_edit}")
                        ss_project_id = project_map_ss.get(selected_project_name_ss_edit)

                        ss_service_name_edit = st.text_input("Service Name/Title*", value=service_data['ServiceName'])
                        
                        current_service_type_edit_val = service_data['ServiceType']
                        ss_service_type_form_val = current_service_type_edit_val if current_service_type_edit_val in service_type_options else "Other"
                        ss_service_type_form_index = service_type_options.index(ss_service_type_form_val)
                        ss_service_type_selected_edit = st.selectbox("Service Type*", service_type_options, index=ss_service_type_form_index, key=f"edit_ss_type_sel_{service_id_to_edit}")
                        ss_service_type_other_val_edit = current_service_type_edit_val if ss_service_type_form_val == "Other" else ""
                        ss_service_type_other_input_edit = st.text_input("Specify Other Service Type", value=ss_service_type_other_val_edit, key=f"edit_ss_type_other_input_{service_id_to_edit}")
                        
                        ss_service_type_final_edit = ss_service_type_selected_edit
                        if ss_service_type_selected_edit == "Other" and ss_service_type_other_input_edit:
                             ss_service_type_final_edit = ss_service_type_other_input_edit

                        ss_service_date_val = datetime.strptime(service_data['ServiceDate'], "%Y-%m-%d").date() if service_data['ServiceDate'] else datetime.now().date()
                        ss_service_date_edit = st.date_input("Service Date*", value=ss_service_date_val)
                        ss_cost_edit = st.number_input("Service Cost (Rs.)*", value=float(service_data.get('Cost', 0.0)), min_value=0.0, format="%.2f")
                        
                        st.write("Current Receipt:")
                        current_receipt_path = service_data['ReceiptPath']
                        # (Display current receipt logic as in View All)
                        if current_receipt_path and os.path.exists(current_receipt_path):
                            if current_receipt_path.lower().endswith(('.png','.jpg','.jpeg')):
                                st.image(Image.open(current_receipt_path), width=150)
                            else: 
                                with open(current_receipt_path, "rb") as fp_edit:
                                    st.download_button( label=f"Download Current Receipt", data=fp_edit, file_name=os.path.basename(current_receipt_path), mime="application/octet-stream", key=f"dl_btn_{service_id_to_edit}" )
                        else: st.text("No receipt on file.")

                        ss_new_receipt_upload = st.file_uploader("Upload New Receipt (Optional - replaces old)", type=['png', 'jpg', 'jpeg', 'pdf'], key=f"edit_ss_receipt_{service_id_to_edit}")
                        ss_description_edit = st.text_area("Description/Notes", value=service_data.get('Description', ''))

                        updated = st.form_submit_button("Update Service")
                        if updated:
                            if not ss_supplier_id or not ss_service_name_edit or not ss_service_type_final_edit or ss_cost_edit < 0:
                                st.error("Supplier, Name, Type, Cost are required.")
                            else:
                                receipt_path_to_save = current_receipt_path
                                if ss_new_receipt_upload:
                                    if current_receipt_path and os.path.exists(current_receipt_path):
                                        try: os.remove(current_receipt_path) 
                                        except Exception as e_del: st.warning(f"Could not remove old receipt {current_receipt_path}: {e_del}")
                                    receipt_path_to_save = save_uploaded_receipt(ss_new_receipt_upload, service_id_to_edit)
                                
                                try:
                                    db.update_supplier_service(
                                        service_id_to_edit, ss_supplier_id, ss_project_id, ss_service_name_edit,
                                        ss_service_type_final_edit, ss_service_date_edit.strftime("%Y-%m-%d"), ss_cost_edit,
                                        receipt_path_to_save, ss_description_edit
                                    )
                                    st.success("Service updated! Note: If cost or critical details changed, associated expense may need manual review/adjustment.")
                                    st.experimental_rerun()
                                except Exception as e: st.error(f"Error updating service: {e}")
    
    elif action_ss == "Delete Service":
        st.subheader("Delete Supplier Service")
        services_list_del = db.get_all_supplier_services()
        if not services_list_del: st.info("No services to delete.")
        else:
            service_options_del = {f"{s['ServiceName']} by {s['SupplierName']} (ID: {s['ServiceID']})": s['ServiceID'] for s in services_list_del}
            selected_service_disp_del = st.selectbox("Select Service to Delete", list(service_options_del.keys()), key="del_ss_select")
            if selected_service_disp_del:
                service_id_to_del = service_options_del[selected_service_disp_del]
                st.warning(f"Are you sure you want to delete this service (ID: {service_id_to_del})? This will also delete its receipt file. The auto-logged expense will NOT be automatically deleted and may require manual action.")
                if st.button("Confirm Delete", key=f"confirm_del_ss_{service_id_to_del}"):
                    try:
                        db.delete_supplier_service(service_id_to_del)
                        st.success("Service deleted successfully!")
                        st.experimental_rerun()
                    except Exception as e: st.error(f"Error deleting service: {e}")

elif choice == "Material Management":
    # ... (Code for Material Management, should be mostly complete from previous responses) ...
    st.header("🧱 Material Management")
    action_mat = st.selectbox("Action", ["View All", "Add New", "Edit Material", "Delete Material"], key="mat_action")
    suppliers_for_mat = db.get_all_suppliers()
    supplier_map_mat = {"None (No Supplier)": None} 
    supplier_map_mat.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_for_mat})
    if action_mat == "View All":
        st.subheader("Existing Materials")
        search_term_mat = st.text_input("Search Materials (Name, Type, Supplier)", key="search_mat_view")
        materials_list = db.get_all_materials(search_term=search_term_mat)
        if materials_list: st.dataframe(db.rows_to_dicts(materials_list), use_container_width=True)
        else: st.info("No materials found.")
    elif action_mat == "Add New":
        st.subheader("Add New Material")
        with st.form("add_material_form_page", clear_on_submit=True): # Unique key
            m_name = st.text_input("Material Name*")
            m_type = st.text_input("Material Type (e.g., Wood, Fabric)")
            m_unit = st.text_input("Unit of Measure (e.g., m, kg, piece)")
            m_cost_unit = st.number_input("Cost Per Unit (Rs.)", min_value=0.0, format="%.2f")
            m_qty = st.number_input("Quantity In Stock", format="%.2f") 
            selected_sup_name_mat = st.selectbox("Supplier", list(supplier_map_mat.keys()), key="add_mat_supplier_page") # Unique key
            m_supplier_id = supplier_map_mat[selected_sup_name_mat]
            submitted = st.form_submit_button("Add Material")
            if submitted:
                if not m_name: st.error("Material Name required.")
                else:
                    try:
                        db.add_material(m_name, m_type, m_unit, m_cost_unit, m_qty, m_supplier_id)
                        st.success("Material added!")
                    except Exception as e: st.error(f"Error: {e}")
    elif action_mat == "Edit Material": # Edit Material as previously defined
        st.subheader("Edit Material")
        materials_list_edit = db.get_all_materials()
        if not materials_list_edit: st.info("No materials to edit.")
        else:
            material_options = {f"{m['MaterialName']} (ID: {m['MaterialID']})": m['MaterialID'] for m in materials_list_edit}
            selected_mat_disp = st.selectbox("Select Material", list(material_options.keys()), key="edit_mat_select_page") # Unique key
            if selected_mat_disp:
                mat_id_to_edit = material_options[selected_mat_disp]
                mat_data = db.get_material_by_id(mat_id_to_edit)
                if mat_data:
                    with st.form(f"edit_material_form_page_{mat_id_to_edit}"): # Unique key
                        m_name = st.text_input("Material Name*", value=mat_data['MaterialName'])
                        m_type = st.text_input("Material Type", value=mat_data['MaterialType'])
                        m_unit = st.text_input("Unit of Measure", value=mat_data['UnitOfMeasure'])
                        m_cost_unit = st.number_input("Cost Per Unit (Rs.)", value=float(mat_data.get('CostPerUnit',0.0)), min_value=0.0, format="%.2f")
                        m_qty = st.number_input("Quantity In Stock", value=float(mat_data.get('QuantityInStock',0.0)), format="%.2f")
                        current_supplier_id = mat_data['SupplierID']
                        current_supplier_key = "None (No Supplier)"
                        material_supplier_keys_list = list(supplier_map_mat.keys())
                        try: mat_supplier_index = material_supplier_keys_list.index(next(k for k,v in supplier_map_mat.items() if v == current_supplier_id))
                        except StopIteration: mat_supplier_index = 0
                        selected_sup_name_mat_edit = st.selectbox("Supplier", material_supplier_keys_list, index=mat_supplier_index, key="edit_mat_supplier_page") # Unique
                        m_supplier_id_edit = supplier_map_mat[selected_sup_name_mat_edit]
                        updated = st.form_submit_button("Update Material")
                        if updated:
                            if not m_name: st.error("Material Name required.")
                            else:
                                try:
                                    db.update_material(mat_id_to_edit, m_name, m_type, m_unit, m_cost_unit, m_qty, m_supplier_id_edit)
                                    st.success("Material updated!")
                                    st.experimental_rerun()
                                except Exception as e: st.error(f"Error: {e}")
    elif action_mat == "Delete Material": # Delete Material as previously defined
        st.subheader("Delete Material")
        materials_list_del = db.get_all_materials()
        if not materials_list_del: st.info("No materials to delete.")
        else:
            material_options_del = {f"{m['MaterialName']} (ID: {m['MaterialID']})": m['MaterialID'] for m in materials_list_del}
            selected_mat_disp_del = st.selectbox("Select Material to Delete", list(material_options_del.keys()), key="del_mat_select_page") # Unique key
            if selected_mat_disp_del:
                mat_id_to_del = material_options_del[selected_mat_disp_del]
                st.warning(f"Are you sure you want to delete {selected_mat_disp_del}?")
                if st.button("Confirm Delete", key=f"confirm_del_mat_page_{mat_id_to_del}"): # Unique key
                    try:
                        db.delete_material(mat_id_to_del)
                        st.success(f"Material {selected_mat_disp_del} deleted!")
                        st.experimental_rerun()
                    except Exception as e: st.error(f"Error deleting material: {e}")

elif choice == "Product Management":
    # ... (Code for Product Management, ensuring all fields from previous example are there and Rs. updates) ...
    st.header("📦 Product Management (Inventory)")
    action_prod = st.selectbox("Action", ["View All", "Add New", "Edit Product", "Delete Product"], key="prod_action_key_main") # Unique key
    suppliers_for_prod = db.get_all_suppliers()
    supplier_map_prod = {"None (No Supplier)": None}
    supplier_map_prod.update({f"{s['SupplierName']} (ID: {s['SupplierID']})": s['SupplierID'] for s in suppliers_for_prod})
    # View All Product code (from previous Rs. version)
    if action_prod == "View All":
        st.subheader("Existing Products")
        search_term_prod = st.text_input("Search Products (Name, SKU, Category, Supplier)", key="search_prod_view_main") # Unique key
        products_list = db.get_all_products(search_term=search_term_prod)
        if products_list:
            df_products = pd.DataFrame(db.rows_to_dicts(products_list))
            cols_to_display_prod = [col for col in df_products.columns if col not in ['ImagePath','SupplierID']] 
            if 'SupplierID' in cols_to_display_prod and 'SupplierName' in df_products.columns : cols_to_display_prod.remove('SupplierID')
            st.dataframe(df_products[cols_to_display_prod], use_container_width=True)
            for prod_row_dict_main in db.rows_to_dicts(products_list): 
                if prod_row_dict_main.get('ImagePath') and os.path.exists(prod_row_dict_main['ImagePath']):
                    with st.expander(f"{prod_row_dict_main['ProductName']} - Image"):
                        try: st.image(Image.open(prod_row_dict_main['ImagePath']), caption=prod_row_dict_main['ProductName'], width=200)
                        except Exception as e_img: st.warning(f"Could not load image: {e_img}")
        else: st.info("No products found.")
    # Add New Product code (from previous Rs. version, ensure save_uploaded_product_image is used)
    elif action_prod == "Add New":
        st.subheader("Add New Product")
        with st.form("add_product_form_main", clear_on_submit=False): # Unique form key, clear_on_submit can be False if using session_state for image name before ID
            p_name = st.text_input("Product Name*")
            p_sku = st.text_input("SKU (Unique)")
            p_desc = st.text_area("Description")
            p_cat = st.text_input("Category (e.g., Sofa, Table)")
            p_mat_type_prod = st.text_input("Material Type (e.g., Wood, Fabric)") 
            p_dims = st.text_input("Dimensions (L x W x H)")
            p_cost = st.number_input("Cost Price (Rs.)", min_value=0.0, format="%.2f")
            p_sell = st.number_input("Selling Price (Rs.)", min_value=0.0, format="%.2f")
            p_qty = st.number_input("Quantity In Stock", min_value=0, step=1)
            p_reorder = st.number_input("Reorder Level", min_value=0, step=1)
            selected_sup_name_prod_add = st.selectbox("Supplier", list(supplier_map_prod.keys()), key="add_prod_supplier_main") # Unique
            p_supplier_id_add = supplier_map_prod[selected_sup_name_prod_add]
            p_uploaded_image_add = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"], key="add_prod_img_main") # Unique
            submitted_add_prod = st.form_submit_button("Add Product")
            if submitted_add_prod:
                if not p_name or not p_sku: st.error("Product Name and SKU required.")
                else:
                    p_image_path_add = None
                    if p_uploaded_image_add: p_image_path_add = save_uploaded_product_image(p_uploaded_image_add, p_sku) # Save with SKU for new
                    try:
                        db.add_product(p_name, p_sku, p_desc, p_cat, p_mat_type_prod, p_dims, p_cost, p_sell, p_qty, p_reorder, p_supplier_id_add, p_image_path_add)
                        st.success(f"Product '{p_name}' added!")
                        # If image was saved with SKU, you might want to update filename to ID post-insert
                        st.experimental_rerun() # To clear form if clear_on_submit is False, or just for refresh
                    except Exception as e_add_prod:
                        st.error(f"Error adding product: {e_add_prod}")
                        if p_image_path_add and os.path.exists(p_image_path_add): os.remove(p_image_path_add) # Clean temp
    # Edit/Delete Product code (from previous Rs. version, ensure save_uploaded_product_image is used for edit, passing product ID)
    elif action_prod == "Edit Product": # As defined in v0.4.1 Rs. Currency
        st.subheader("Edit Product")
        products_list_edit_main = db.get_all_products()
        if not products_list_edit_main: st.info("No products to edit.")
        else:
            product_options_edit_main = {f"{p['ProductName']} (SKU: {p['SKU']}, ID: {p['ProductID']})": p['ProductID'] for p in products_list_edit_main}
            selected_prod_disp_edit_main = st.selectbox("Select Product to Edit", list(product_options_edit_main.keys()), key="edit_prod_select_key_main_page") # Unique key
            if selected_prod_disp_edit_main:
                prod_id_to_edit_main = product_options_edit_main[selected_prod_disp_edit_main]
                prod_data_edit_main = db.get_product_by_id(prod_id_to_edit_main)
                if prod_data_edit_main:
                    with st.form(f"edit_product_form_main_page_{prod_id_to_edit_main}"): # Unique key
                        p_name_edit = st.text_input("Product Name*", value=prod_data_edit_main['ProductName'])
                        p_sku_edit = st.text_input("SKU (Unique)", value=prod_data_edit_main['SKU'])
                        p_desc_edit = st.text_area("Description", value=prod_data_edit_main['Description'])
                        p_cat_edit = st.text_input("Category", value=prod_data_edit_main.get('Category',''))
                        p_mat_type_prod_edit = st.text_input("Material Type", value=prod_data_edit_main.get('MaterialType',''))
                        p_dims_edit = st.text_input("Dimensions", value=prod_data_edit_main.get('Dimensions',''))
                        p_cost_edit = st.number_input("Cost Price (Rs.)", value=float(prod_data_edit_main.get('CostPrice',0.0)), min_value=0.0, format="%.2f")
                        p_sell_edit = st.number_input("Selling Price (Rs.)", value=float(prod_data_edit_main.get('SellingPrice',0.0)), min_value=0.0, format="%.2f")
                        p_qty_edit = st.number_input("Quantity In Stock", value=int(prod_data_edit_main.get('QuantityInStock',0)), min_value=0, step=1)
                        p_reorder_edit = st.number_input("Reorder Level", value=int(prod_data_edit_main.get('ReorderLevel',0)), min_value=0, step=1)
                        current_sup_id_prod_edit = prod_data_edit_main['SupplierID']
                        current_sup_key_prod_edit = "None (No Supplier)"
                        product_supplier_keys_list = list(supplier_map_prod.keys())
                        try: prod_supplier_index = product_supplier_keys_list.index(next(k for k,v in supplier_map_prod.items() if v == current_sup_id_prod_edit))
                        except StopIteration: prod_supplier_index = 0
                        selected_sup_name_prod_edit_page = st.selectbox("Supplier", product_supplier_keys_list, index=prod_supplier_index, key="edit_prod_supplier_main_page") # Unique
                        p_supplier_id_edit = supplier_map_prod[selected_sup_name_prod_edit_page]
                        st.write("Current Image:")
                        current_image_path_edit = prod_data_edit_main['ImagePath']
                        if current_image_path_edit and os.path.exists(current_image_path_edit):
                            try: st.image(Image.open(current_image_path_edit), width=150)
                            except Exception: st.text("Could not load current image.")
                        else: st.text("No image.")
                        p_new_uploaded_image_edit = st.file_uploader("Upload New Image (Optional - replaces old)", type=["png", "jpg", "jpeg"], key=f"edit_img_upload_main_page_{prod_id_to_edit_main}") # Unique key
                        updated_prod = st.form_submit_button("Update Product")
                        if updated_prod:
                            if not p_name_edit or not p_sku_edit: st.error("Name and SKU required.")
                            else:
                                image_path_to_save_edit = current_image_path_edit
                                if p_new_uploaded_image_edit:
                                    if current_image_path_edit and os.path.exists(current_image_path_edit) and current_image_path_edit != f"product_{prod_id_to_edit_main}{os.path.splitext(p_new_uploaded_image_edit.name)[1]}": # remove if filename changes significantly or always if replacing.
                                        try: os.remove(current_image_path_edit) 
                                        except Exception as e_del_img: st.warning(f"Old image removal issue: {e_del_img}")
                                    image_path_to_save_edit = save_uploaded_product_image(p_new_uploaded_image_edit, prod_id_to_edit_main) # Save with Product ID
                                try:
                                    db.update_product(prod_id_to_edit_main, p_name_edit, p_sku_edit, p_desc_edit, p_cat_edit, p_mat_type_prod_edit, p_dims_edit, p_cost_edit, p_sell_edit, p_qty_edit, p_reorder_edit, p_supplier_id_edit, image_path_to_save_edit)
                                    st.success("Product updated!")
                                    st.experimental_rerun()
                                except Exception as e_upd_prod: st.error(f"Error updating: {e_upd_prod}")
    elif action_prod == "Delete Product": # As defined in v0.4.1 Rs. Currency
        st.subheader("Delete Product")
        products_list_del_main = db.get_all_products()
        if not products_list_del_main: st.info("No products to delete.")
        else:
            product_options_del_main = {f"{p['ProductName']} (SKU: {p['SKU']}, ID: {p['ProductID']})": p['ProductID'] for p in products_list_del_main}
            selected_prod_disp_del_main = st.selectbox("Select Product to Delete", list(product_options_del_main.keys()), key="del_prod_select_key_main_page") # Unique
            if selected_prod_disp_del_main:
                prod_id_to_del_main = product_options_del_main[selected_prod_disp_del_main]
                st.warning(f"Are you sure you want to delete {selected_prod_disp_del_main}? This cannot be undone and will also delete its image.")
                if st.button("Confirm Delete", key=f"confirm_del_prod_main_page_{prod_id_to_del_main}"): # Unique
                    try:
                        db.delete_product(prod_id_to_del_main)
                        st.success("Product deleted successfully!")
                        st.experimental_rerun()
                    except Exception as e_del_prod_main: st.error(f"Error deleting product: {e_del_prod_main}")

elif choice == "Project Management":
    # ... (Code for Project Management, as in v0.4.1 Rs. Currency) ...
    st.header("🛠️ Project Management")
    action_proj = st.selectbox("Action", ["View All", "Add New", "Edit Project", "Delete Project"], key="proj_action_main_key") # Unique
    customers_for_proj = db.get_all_customers()
    customer_map_proj = {"None": None}
    customer_map_proj.update({f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_proj})
    project_status_options = ["Planning", "In Progress", "On Hold", "Completed", "Cancelled"]
    # View, Add, Edit, Delete logic as in previous versions, ensuring all Rs. labels for budget etc.
    if action_proj == "View All":
        st.subheader("Existing Projects")
        search_term_proj = st.text_input("Search Projects (Name, Customer, Status)", key="search_proj_view_main_key") # Unique
        projects_list = db.get_all_projects(search_term=search_term_proj)
        if projects_list: st.dataframe(db.rows_to_dicts(projects_list), use_container_width=True)
        else: st.info("No projects found.")
    elif action_proj == "Add New":
        st.subheader("Add New Project")
        with st.form("add_project_form_main_key", clear_on_submit=True): # Unique
            pr_name = st.text_input("Project Name*")
            selected_cust_name_proj = st.selectbox("Customer", list(customer_map_proj.keys()), key="add_proj_customer_main_key") # Unique
            pr_customer_id = customer_map_proj[selected_cust_name_proj]
            col_start_proj, col_end_proj = st.columns(2)
            pr_start_date = col_start_proj.date_input("Start Date", datetime.now().date())
            pr_end_date = col_end_proj.date_input("Expected End Date", (datetime.now() + pd.Timedelta(days=30)).date() )
            pr_status = st.selectbox("Status", project_status_options)
            pr_budget = st.number_input("Budget (Rs.)", min_value=0.0, format="%.2f")
            pr_desc = st.text_area("Description")
            submitted_proj = st.form_submit_button("Add Project")
            if submitted_proj:
                if not pr_name: st.error("Project Name required.")
                else:
                    try:
                        db.add_project(pr_name, pr_customer_id, pr_start_date.strftime("%Y-%m-%d") if pr_start_date else None, pr_end_date.strftime("%Y-%m-%d") if pr_end_date else None, pr_status, pr_budget, pr_desc)
                        st.success("Project added!")
                    except Exception as e_proj_add: st.error(f"Error: {e_proj_add}")
    elif action_proj == "Edit Project": # As in v0.4.1 Rs. currency
        st.subheader("Edit Project")
        projects_list_edit_main = db.get_all_projects()
        if not projects_list_edit_main: st.info("No projects to edit.")
        else:
            project_options_edit_main_page = {f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_list_edit_main}
            selected_proj_disp_edit_main_page = st.selectbox("Select Project", list(project_options_edit_main_page.keys()), key="edit_proj_select_main_key") # Unique
            if selected_proj_disp_edit_main_page:
                proj_id_to_edit_main_page = project_options_edit_main_page[selected_proj_disp_edit_main_page]
                proj_data_main_page = db.get_project_by_id(proj_id_to_edit_main_page)
                if proj_data_main_page:
                    with st.form(f"edit_project_form_main_page_{proj_id_to_edit_main_page}"): # Unique
                        pr_name_edit = st.text_input("Project Name*", value=proj_data_main_page['ProjectName'])
                        current_cust_id_proj_edit = proj_data_main_page['CustomerID']
                        current_cust_key_proj_edit = "None"
                        project_customer_keys_list = list(customer_map_proj.keys())
                        try: proj_customer_index = project_customer_keys_list.index(next(k for k,v in customer_map_proj.items() if v == current_cust_id_proj_edit))
                        except StopIteration: proj_customer_index = 0
                        selected_cust_name_proj_edit_page = st.selectbox("Customer", project_customer_keys_list, index=proj_customer_index, key="edit_proj_customer_main_page") # Unique
                        pr_customer_id_edit = customer_map_proj[selected_cust_name_proj_edit_page]
                        col_start_proj_edit, col_end_proj_edit = st.columns(2)
                        pr_start_date_val_edit = datetime.strptime(proj_data_main_page['StartDate'], "%Y-%m-%d").date() if proj_data_main_page['StartDate'] else None
                        pr_end_date_val_edit = datetime.strptime(proj_data_main_page['EndDate'], "%Y-%m-%d").date() if proj_data_main_page['EndDate'] else None
                        pr_start_date_edit = col_start_proj_edit.date_input("Start Date", value=pr_start_date_val_edit)
                        pr_end_date_edit = col_end_proj_edit.date_input("Expected End Date", value=pr_end_date_val_edit)
                        pr_status_edit = st.selectbox("Status", project_status_options, index=project_status_options.index(proj_data_main_page['Status']) if proj_data_main_page['Status'] in project_status_options else 0)
                        pr_budget_edit = st.number_input("Budget (Rs.)", value=float(proj_data_main_page.get('Budget',0.0)), min_value=0.0, format="%.2f")
                        pr_desc_edit = st.text_area("Description", value=proj_data_main_page['Description'])
                        updated_proj_edit = st.form_submit_button("Update Project")
                        if updated_proj_edit:
                            if not pr_name_edit: st.error("Project Name required.")
                            else:
                                try:
                                    db.update_project(proj_id_to_edit_main_page, pr_name_edit, pr_customer_id_edit, pr_start_date_edit.strftime("%Y-%m-%d") if pr_start_date_edit else None, pr_end_date_edit.strftime("%Y-%m-%d") if pr_end_date_edit else None, pr_status_edit, pr_budget_edit, pr_desc_edit)
                                    st.success("Project updated!")
                                    st.experimental_rerun()
                                except Exception as e_proj_edit: st.error(f"Error: {e_proj_edit}")
    elif action_proj == "Delete Project": # Delete logic
        st.subheader("Delete Project")
        projects_list_del_main = db.get_all_projects()
        if not projects_list_del_main: st.info("No projects to delete.")
        else:
            project_options_del_main_page = {f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_list_del_main}
            selected_proj_disp_del_main_page = st.selectbox("Select Project to Delete", list(project_options_del_main_page.keys()), key="del_proj_select_main_key") # Unique
            if selected_proj_disp_del_main_page:
                proj_id_to_del_main_page = project_options_del_main_page[selected_proj_disp_del_main_page]
                st.warning(f"Are you sure you want to delete project '{selected_proj_disp_del_main_page}'? This might affect orders/expenses linked to it.")
                if st.button("Confirm Delete Project", key=f"confirm_del_proj_main_page_{proj_id_to_del_main_page}"): # Unique
                    try:
                        db.delete_project(proj_id_to_del_main_page)
                        st.success("Project deleted!")
                        st.experimental_rerun()
                    except Exception as e_del_proj_main: st.error(f"Error deleting project: {e_del_proj_main}")


elif choice == "Sales Book (Orders)":
    # ... (Code for Sales Book, as in v0.4.1 Rs. Currency, ensuring unique keys and Rs. displays) ...
    st.header("🛒 Sales Book (Orders)")
    action_order_main = st.selectbox("Action", ["View All Orders", "Create New Order", "Edit Order (Basic Info)"], key="order_action_main_key") # Unique
    if action_order_main == "View All Orders":
        st.subheader("Existing Orders")
        all_db_orders_main = db.get_all_orders()
        if all_db_orders_main:
            st.dataframe(db.rows_to_dicts(all_db_orders_main), use_container_width=True)
            order_ids_for_view_main = [o['OrderID'] for o in all_db_orders_main]
            if order_ids_for_view_main:
                selected_order_id_view_main = st.selectbox("Select Order ID to view items", order_ids_for_view_main, key="view_order_items_select_db_main_key") # Unique
                if selected_order_id_view_main:
                    items_for_order_main = db.get_order_items_by_order_id(selected_order_id_view_main)
                    if items_for_order_main:
                        st.write(f"Items for Order ID: {selected_order_id_view_main}")
                        st.dataframe(db.rows_to_dicts(items_for_order_main), use_container_width=True)
                    else: st.info("No items found for this order.")
        else: st.info("No orders recorded yet.")
    elif action_order_main == "Create New Order": # As in v0.4.1 Rs Currency, ensuring unique keys for widgets
        st.subheader("Create New Order")
        customers_for_order_main = db.get_all_customers()
        customer_map_order_main = {"None": None}
        customer_map_order_main.update({f"{c['CustomerName']} (ID: {c['CustomerID']})": c['CustomerID'] for c in customers_for_order_main})
        projects_for_order_main = db.get_all_projects()
        project_map_order_main = {"None (No Project)": None}
        project_map_order_main.update({f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_for_order_main})
        order_status_options_main = ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
        payment_status_options_main = ["Unpaid", "Partially Paid", "Paid", "Refunded"]
        with st.form("add_order_form_db_main_key", clear_on_submit=False): # Unique key
            o_order_date_main = st.date_input("Order Date", datetime.now().date())
            selected_cust_name_order_main = st.selectbox("Customer*", list(customer_map_order_main.keys()), key="order_cust_db_select_main_key") # Unique
            o_customer_id_main = customer_map_order_main.get(selected_cust_name_order_main)
            selected_proj_name_order_main = st.selectbox("Associated Project (Optional)", list(project_map_order_main.keys()), key="order_proj_db_select_main_key") # Unique
            o_project_id_main = project_map_order_main.get(selected_proj_name_order_main)
            col_ord_stat1_main, col_ord_stat2_main = st.columns(2)
            o_order_status_main = col_ord_stat1_main.selectbox("Order Status", order_status_options_main)
            o_payment_status_main = col_ord_stat2_main.selectbox("Payment Status", payment_status_options_main)
            initial_shipping_address_main = ""
            if o_customer_id_main:
                cust_details_for_addr_main = db.get_customer_by_id(o_customer_id_main)
                if cust_details_for_addr_main: initial_shipping_address_main = cust_details_for_addr_main.get('ShippingAddress') or cust_details_for_addr_main.get('BillingAddress', "")
            o_shipping_address_main = st.text_area("Shipping Address", value=initial_shipping_address_main, key="order_ship_addr_main_input_key") # Unique
            o_notes_main = st.text_area("Order Notes")
            st.markdown("---"); st.subheader("Order Items")
            if 'current_order_items_main' not in st.session_state: st.session_state.current_order_items_main = []
            products_for_items_order_main = db.get_all_products()
            product_map_order_items_main = {"Select Product": None}
            product_map_order_items_main.update({f"{p['ProductName']} (ID: {p['ProductID']}, Price: Rs. {p['SellingPrice']:.2f}, Stock: {p['QuantityInStock']})": p['ProductID'] for p in products_for_items_order_main})
            item_cols_main = st.columns([3, 1, 1, 1, 0.5])
            selected_prod_disp_item_main = item_cols_main[0].selectbox("Product", list(product_map_order_items_main.keys()), key="order_item_prod_select_key_main_new") # Unique
            qty_item_main = item_cols_main[1].number_input("Qty", min_value=1, value=1, step=1, key="order_item_qty_val_main_new") # Unique
            prod_id_for_price_main = product_map_order_items_main.get(selected_prod_disp_item_main)
            default_unit_price_main = 0.0
            if prod_id_for_price_main:
                prod_details_main = db.get_product_by_id(prod_id_for_price_main)
                if prod_details_main: default_unit_price_main = float(prod_details_main['SellingPrice'])
            unit_price_item_override_main = item_cols_main[2].number_input("Unit Price (Rs.)", min_value=0.0, value=default_unit_price_main, format="%.2f", key="order_item_price_val_main_new") # Unique
            discount_item_val_main = item_cols_main[3].number_input("Discount (Rs.)", min_value=0.0, value=0.0, format="%.2f", key="order_item_disc_val_main_new") # Unique
            if item_cols_main[4].button("➕ Add", key="order_add_item_button_key_main"): # Unique
                if prod_id_for_price_main and qty_item_main > 0:
                    prod_details_add_main = db.get_product_by_id(prod_id_for_price_main)
                    if prod_details_add_main['QuantityInStock'] < qty_item_main: st.warning(f"Not enough stock for {prod_details_add_main['ProductName']} (Available: {prod_details_add_main['QuantityInStock']}).")
                    else:
                        st.session_state.current_order_items_main.append({'ProductID': prod_id_for_price_main, 'ProductName': prod_details_add_main['ProductName'], 'QuantitySold': qty_item_main, 'UnitPriceAtSale': unit_price_item_override_main, 'Discount': discount_item_val_main, 'LineTotal': (unit_price_item_override_main * qty_item_main) - discount_item_val_main})
                        st.experimental_rerun() 
                else: st.warning("Please select a product and quantity.")
            if st.session_state.current_order_items_main:
                st.markdown("**Items in this Order:**")
                temp_items_df_main = pd.DataFrame(st.session_state.current_order_items_main)
                temp_items_df_main['UnitPriceAtSale_Display'] = temp_items_df_main['UnitPriceAtSale'].apply(lambda x: f"Rs. {x:,.2f}")
                temp_items_df_main['Discount_Display'] = temp_items_df_main['Discount'].apply(lambda x: f"Rs. {x:,.2f}")
                temp_items_df_main['LineTotal_Display'] = temp_items_df_main['LineTotal'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(temp_items_df_main[['ProductName', 'QuantitySold', 'UnitPriceAtSale_Display', 'Discount_Display', 'LineTotal_Display']], use_container_width=True)
                current_total_amount_numeric_main = sum(item['LineTotal'] for item in st.session_state.current_order_items_main)
                st.metric("Calculated Order Total", f"Rs. {current_total_amount_numeric_main:,.2f}")
            submitted_order_db_main = st.form_submit_button("💾 Create Order")
            if submitted_order_db_main:
                if not o_customer_id_main: st.error("Customer is required.")
                elif not st.session_state.current_order_items_main: st.error("Order must have at least one item.")
                else:
                    final_shipping_address_main_val = st.session_state.get("order_ship_addr_main_input_key", initial_shipping_address_main)
                    try:
                        new_order_id_main = db.add_order(o_order_date_main.strftime("%Y-%m-%d"), o_customer_id_main, o_project_id_main, o_order_status_main, 0, o_payment_status_main, final_shipping_address_main_val, o_notes_main)
                        for item_data_main in st.session_state.current_order_items_main:
                            db.add_order_item(new_order_id_main, item_data_main['ProductID'], item_data_main['QuantitySold'], item_data_main['UnitPriceAtSale'], item_data_main['Discount'])
                            db.update_product_stock(item_data_main['ProductID'], -item_data_main['QuantitySold'])
                        db.update_order_total(new_order_id_main) 
                        st.success(f"Order (ID: {new_order_id_main}) created successfully!")
                        st.session_state.current_order_items_main = [] 
                        st.experimental_rerun()
                    except Exception as e_ord_add: st.error(f"Error creating order: {e_ord_add}")
    # Edit Order (Basic Info) can be added here, but item editing is complex

elif choice == "Expense Tracking":
    # ... (Code for Expense Tracking, as in v0.5 - Supplier Services, ensuring Rs. and unique keys) ...
    st.header("💸 Expense Tracking")
    projects_for_exp_main = db.get_all_projects() # Use different variable name to avoid scope collision if any
    project_map_exp_main_scope = {"None (No Project)": None}
    project_map_exp_main_scope.update({f"{p['ProjectName']} (ID: {p['ProjectID']})": p['ProjectID'] for p in projects_for_exp_main})
    action_exp_main_page = st.selectbox("Action", ["View All", "Add New (Manual)"], key="exp_action_main_page_key") # Unique
    if action_exp_main_page == "View All":
        st.subheader("Recorded Expenses")
        all_db_expenses_main_page = db.get_all_expenses()
        if all_db_expenses_main_page:
            df_expenses_main_page = pd.DataFrame(db.rows_to_dicts(all_db_expenses_main_page))
            if 'Amount' in df_expenses_main_page.columns: df_expenses_main_page['Amount_Display'] = df_expenses_main_page['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
            cols_exp_disp_main = ['ExpenseID', 'ExpenseDate', 'Description', 'Category', 'Amount_Display', 'Vendor', 'ProjectName', 'ReceiptReference']
            cols_exp_disp_filt_main = [col for col in cols_exp_disp_main if col in df_expenses_main_page.columns]
            st.dataframe(df_expenses_main_page[cols_exp_disp_filt_main], use_container_width=True)
        else: st.info("No expenses recorded yet.")
    elif action_exp_main_page == "Add New (Manual)":
        st.subheader("Add New Manual Expense")
        with st.form("add_manual_expense_form_db_main_key", clear_on_submit=True): # Unique key
            exp_date_man_main = st.date_input("Expense Date", datetime.now().date())
            desc_exp_man_main = st.text_input("Description*")
            cat_exp_opts_man_main = ["Operational", "Marketing", "COGS", "Salaries", "Utilities", "Rent", "Travel", "Manual Adjustment", "Other"]
            cat_exp_man_main = st.selectbox("Category", cat_exp_opts_man_main)
            amt_exp_man_main = st.number_input("Amount (Rs.)*", min_value=0.01, format="%.2f")
            vendor_exp_man_main = st.text_input("Vendor/Payee")
            selected_proj_name_exp_man_main = st.selectbox("Associated Project (Optional)", list(project_map_exp_main_scope.keys()), key="exp_manual_proj_db_select_main_key") # Unique
            exp_project_id_man_main = project_map_exp_main_scope.get(selected_proj_name_exp_man_main)
            receipt_ref_exp_man_main = st.text_input("Receipt Reference")
            submitted_exp_man_main = st.form_submit_button("Add Manual Expense")
            if submitted_exp_man_main:
                if not desc_exp_man_main or amt_exp_man_main <= 0: st.error("Description and a valid Amount are required.")
                else:
                    try:
                        db.add_expense(exp_date_man_main.strftime("%Y-%m-%d"), desc_exp_man_main, cat_exp_man_main, amt_exp_man_main, vendor_exp_man_main, exp_project_id_man_main, receipt_ref_exp_man_main)
                        st.success("Manual expense added successfully!")
                    except Exception as e_exp_add: st.error(f"Error: {e_exp_add}")

elif choice == "Reports":
    # ... (Code for Reports, as in v0.4.1 Rs. Currency) ...
    st.header("📈 Reports")
    st.info("Reporting section requires further development to query and visualize data.")
    report_type_main = st.selectbox("Select Report Type (Basic Examples)", ["Overall Financial Summary", "Sales by Product (Placeholder)", "Inventory Status (Placeholder)"])
    if report_type_main == "Overall Financial Summary":
        orders_main_rep = db.get_all_orders()
        expenses_main_rep = db.get_all_expenses()
        total_revenue_main_rep = sum(o['TotalAmount'] for o in orders_main_rep if o['TotalAmount']) if orders_main_rep else 0
        total_operational_expenses_main_rep = sum(e['Amount'] for e in expenses_main_rep if e['Amount']) if expenses_main_rep else 0
        st.metric("Total Revenue", f"Rs. {total_revenue_main_rep:,.2f}")
        st.metric("Total Operational Expenses", f"Rs. {total_operational_expenses_main_rep:,.2f}")
        st.metric("Gross Operating Difference", f"Rs. {total_revenue_main_rep - total_operational_expenses_main_rep:,.2f}")
        st.caption("Note: This is a very simplified summary. Proper P/L requires COGS.")


st.sidebar.markdown("---")
st.sidebar.info("Management System v0.5 - Rs.")
