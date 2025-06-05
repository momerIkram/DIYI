import sqlite3
import os
from datetime import datetime

DATABASE_DIR = "data"
DATABASE_NAME = os.path.join(DATABASE_DIR, "furniture_management.db")
IMAGE_DIR = "images" # For product images
RECEIPT_DIR = os.path.join("data", "receipts") # For service receipts

if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
if not os.path.exists(RECEIPT_DIR): # Create receipts directory
    os.makedirs(RECEIPT_DIR)


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # ... (all existing table creations: customers, suppliers, products, materials, projects, orders, order_items, expenses) ...
    # --- Supplier Services Table ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS supplier_services (
        ServiceID INTEGER PRIMARY KEY AUTOINCREMENT,
        SupplierID INTEGER NOT NULL,
        ProjectID INTEGER, -- Optional link to a customer project
        ServiceName TEXT NOT NULL, -- e.g., "Oak Wood Cutting for Project Alpha" or "Standard Polishing Job"
        ServiceType TEXT NOT NULL, -- e.g., Paint Work, Wood Cutting, Polishing, Stitching
        ServiceDate TEXT NOT NULL, -- Date the service was rendered/billed
        Cost REAL NOT NULL,
        ReceiptPath TEXT, -- Path to an uploaded receipt image/PDF
        Description TEXT,
        IsExpenseLogged INTEGER DEFAULT 0, -- Boolean (0 for False, 1 for True)
        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID) ON DELETE CASCADE, -- If supplier deleted, their service records are too (or SET NULL if preferred)
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE SET NULL
    )
    ''')
    conn.commit()
    conn.close()

# --- (All existing CRUD functions for customers, suppliers, products, materials, projects, orders, order_items) ---

# --- Expense CRUD (Ensure add_expense can be called internally) ---
def add_expense(exp_date, desc, category, amount, vendor, project_id, receipt_ref, is_internal_call=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO expenses (ExpenseDate, Description, Category, Amount, Vendor, ProjectID, ReceiptReference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (exp_date, desc, category, amount, vendor, project_id, receipt_ref))
        expense_id = cursor.lastrowid
        conn.commit()
        return expense_id
    except Exception as e:
        conn.rollback()
        # For internal calls, we might not want to raise UI errors directly but log them or handle differently
        if not is_internal_call:
            raise e # Re-raise for UI forms
        else:
            print(f"Internal error adding expense: {e}") # Log for server-side/internal calls
            return None # Indicate failure
    finally:
        conn.close()

# --- Supplier Service CRUD ---
def add_supplier_service(supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    service_id = None
    expense_logged_successfully = False
    try:
        cursor.execute('''
        INSERT INTO supplier_services (SupplierID, ProjectID, ServiceName, ServiceType, ServiceDate, Cost, ReceiptPath, Description, IsExpenseLogged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0) 
        ''', (supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description))
        service_id = cursor.lastrowid
        
        # Automatically log this service as an expense
        if cost > 0 and service_id:
            supplier = get_supplier_by_id(supplier_id) # Get supplier name for expense vendor field
            supplier_name_for_expense = supplier['SupplierName'] if supplier else f"Supplier ID: {supplier_id}"
            
            expense_desc = f"Service: {service_name} by {supplier_name_for_expense}"
            if service_type:
                expense_desc += f" ({service_type})"

            new_expense_id = add_expense(
                exp_date=service_date,
                desc=expense_desc,
                category="Supplier Services", # New category for expenses
                amount=cost,
                vendor=supplier_name_for_expense, # Store supplier name
                project_id=project_id,
                receipt_ref=f"Service ID: {service_id}" + (f", Receipt: {os.path.basename(receipt_path)}" if receipt_path else ""),
                is_internal_call=True # Indicate this is not from a direct user form for expenses
            )
            if new_expense_id:
                cursor.execute("UPDATE supplier_services SET IsExpenseLogged = 1 WHERE ServiceID = ?", (service_id,))
                expense_logged_successfully = True
            else:
                # Optional: Handle failure to log expense more gracefully, maybe rollback service add or warn user
                print(f"Warning: Service ID {service_id} added, but failed to auto-log expense.")
                
        conn.commit()
        return service_id, expense_logged_successfully
    except Exception as e:
        conn.rollback()
        raise e # Re-raise the original error for the UI
    finally:
        conn.close()

def get_all_supplier_services(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT ss.*, s.SupplierName, p.ProjectName
    FROM supplier_services ss
    JOIN suppliers s ON ss.SupplierID = s.SupplierID
    LEFT JOIN projects p ON ss.ProjectID = p.ProjectID
    """
    params = []
    # Add search conditions if search_term is provided
    if search_term:
        query += " WHERE (ss.ServiceName LIKE ? OR ss.ServiceType LIKE ? OR s.SupplierName LIKE ? OR p.ProjectName LIKE ? OR ss.Description LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term])
    query += " ORDER BY ss.ServiceDate DESC"
    cursor.execute(query, params)
    services = cursor.fetchall()
    conn.close()
    return services

def get_supplier_service_by_id(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT ss.*, s.SupplierName, p.ProjectName
    FROM supplier_services ss
    JOIN suppliers s ON ss.SupplierID = s.SupplierID
    LEFT JOIN projects p ON ss.ProjectID = p.ProjectID
    WHERE ss.ServiceID = ?
    """, (service_id,))
    service = cursor.fetchone()
    conn.close()
    return service

def update_supplier_service(service_id, supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Note: If cost or critical details change, re-evaluating the linked expense might be needed, which can get complex.
    # For now, we'll update the service record. Manual adjustment of linked expense might be necessary if not handled.
    # Or, delete old expense and create new one if cost/date changes. Simpler: just update the service for now.
    try:
        cursor.execute('''
        UPDATE supplier_services
        SET SupplierID = ?, ProjectID = ?, ServiceName = ?, ServiceType = ?, ServiceDate = ?,
            Cost = ?, ReceiptPath = ?, Description = ? 
        WHERE ServiceID = ?
        ''', (supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description, service_id))
        
        # Potentially re-evaluate IsExpenseLogged if cost changed from/to 0, or if critical info changed
        # This is a simplification. A more robust system would update or delete/recreate the associated expense record.
        current_service = get_supplier_service_by_id(service_id) # fetch to check IsExpenseLogged and old cost
        if current_service and current_service['IsExpenseLogged'] and current_service['Cost'] != cost :
             st.warning(f"Service {service_id} cost updated. Please manually review/update linked expense record (ID usually related to service ID description in expenses).") # Add streamlit reference for UI only in app.py
             print(f"Warning: Service {service_id} cost updated. Please manually review/update linked expense record.")


        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_supplier_service(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        service_info = get_supplier_service_by_id(service_id) # Get info before deleting for receipt path
        
        # Important: Decide on policy for linked expense.
        # Option 1: Delete linked expense (hard to find without specific link, ServiceID in receipt_ref helps)
        # Option 2: Leave linked expense and user has to manually delete/adjust it.
        # Option 3: Add a "Cancelled" status to the expense if service is deleted.
        # For simplicity here, we delete the service record and its receipt. User should manage related expense if needed.
        # A better system would involve a direct link (e.g., Expense.RelatedServiceID)

        if service_info and service_info['ReceiptPath'] and os.path.exists(service_info['ReceiptPath']):
            try:
                os.remove(service_info['ReceiptPath'])
            except OSError as e:
                print(f"Error deleting receipt file {service_info['ReceiptPath']}: {e}")
        
        cursor.execute("DELETE FROM supplier_services WHERE ServiceID = ?", (service_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- (get_all_expenses() remains the same) ---

# Helper and init_db as before
def rows_to_dicts(rows):
    return [dict(row) for row in rows]

init_db()
