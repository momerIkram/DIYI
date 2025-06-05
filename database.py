import sqlite3
import os
from datetime import datetime

DATABASE_DIR = "data"
DATABASE_NAME = os.path.join(DATABASE_DIR, "furniture_management.db")
IMAGE_DIR = "images"
RECEIPT_DIR = os.path.join("data", "receipts")

if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
if not os.path.exists(RECEIPT_DIR):
    os.makedirs(RECEIPT_DIR)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    # Enable foreign key support for every connection
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Customers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        CustomerName TEXT NOT NULL,
        Email TEXT,
        Phone TEXT,
        BillingAddress TEXT,
        ShippingAddress TEXT,
        RegistrationDate TEXT,
        Notes TEXT
    )
    ''')

    # Suppliers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        SupplierName TEXT NOT NULL UNIQUE,
        ContactPerson TEXT,
        Email TEXT,
        Phone TEXT,
        Address TEXT
    )
    ''')

    # Products (Furniture)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        ProductName TEXT NOT NULL,
        SKU TEXT UNIQUE,
        Description TEXT,
        Category TEXT,
        MaterialType TEXT,
        Dimensions TEXT,
        CostPrice REAL,
        SellingPrice REAL,
        QuantityInStock INTEGER,
        ReorderLevel INTEGER,
        SupplierID INTEGER,
        ImagePath TEXT,
        LastStockUpdate TEXT,
        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID) ON DELETE SET NULL
    )
    ''')

    # Materials
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        MaterialID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        MaterialName TEXT NOT NULL UNIQUE,
        MaterialType TEXT,
        UnitOfMeasure TEXT,
        CostPerUnit REAL,
        QuantityInStock REAL,
        SupplierID INTEGER,
        LastStockUpdate TEXT,
        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID) ON DELETE SET NULL
    )
    ''')

    # Projects
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        ProjectName TEXT NOT NULL,
        CustomerID INTEGER,
        StartDate TEXT,
        EndDate TEXT,
        Status TEXT,
        Budget REAL,
        Description TEXT,
        FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID) ON DELETE SET NULL
    )
    ''')

    # Supplier Services
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS supplier_services (
        ServiceID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        SupplierID INTEGER NOT NULL,
        ProjectID INTEGER,
        ServiceName TEXT NOT NULL,
        ServiceType TEXT NOT NULL,
        ServiceDate TEXT NOT NULL,
        Cost REAL NOT NULL,
        ReceiptPath TEXT,
        Description TEXT,
        IsExpenseLogged INTEGER DEFAULT 0,
        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID) ON DELETE CASCADE,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE SET NULL
    )
    ''')

    # Orders
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        OrderDate TEXT NOT NULL,
        CustomerID INTEGER,
        ProjectID INTEGER,
        OrderStatus TEXT,
        TotalAmount REAL,
        PaymentStatus TEXT,
        ShippingAddress TEXT,
        Notes TEXT,
        FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID) ON DELETE SET NULL,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE SET NULL
    )
    ''')

    # Order Items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        OrderItemID INTEGER PRIMARY KEY AUTOINCREMENT,
        OrderID INTEGER NOT NULL,
        ProductID INTEGER NOT NULL,
        QuantitySold INTEGER,
        UnitPriceAtSale REAL,
        Discount REAL,
        LineTotal REAL,
        FOREIGN KEY (OrderID) REFERENCES orders (OrderID) ON DELETE CASCADE,
        FOREIGN KEY (ProductID) REFERENCES products (ProductID) ON DELETE RESTRICT
    )
    ''')

    # Expenses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        ExpenseID INTEGER PRIMARY KEY AUTOINCREMENT,
        ReferenceID TEXT UNIQUE,
        ExpenseDate TEXT NOT NULL,
        Description TEXT NOT NULL,
        Category TEXT,
        Amount REAL NOT NULL,
        Vendor TEXT,
        ProjectID INTEGER,
        ReceiptReference TEXT,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE SET NULL
    )
    ''')

    # Invoices (New Table)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        InvoiceID INTEGER PRIMARY KEY AUTOINCREMENT,
        InvoiceReferenceID TEXT UNIQUE NOT NULL,
        ProjectID INTEGER NOT NULL,
        CustomerID INTEGER NOT NULL,
        IssueDate TEXT NOT NULL,
        DueDate TEXT NOT NULL,
        PaymentDate TEXT,
        TotalAmount REAL NOT NULL,
        Status TEXT NOT NULL, -- e.g., Draft, Sent, Paid, Overdue, Cancelled
        Notes TEXT,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE RESTRICT, -- Don't delete project if invoices exist
        FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID) ON DELETE RESTRICT -- Don't delete customer if invoices exist
    )
    ''')

    conn.commit()
    conn.close()


# --- Customer CRUD ---
def add_customer(name, email, phone, reference_id_input, bill_addr, ship_addr, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        INSERT INTO customers (CustomerName, Email, Phone, BillingAddress, ShippingAddress, RegistrationDate, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, bill_addr, ship_addr or bill_addr, reg_date, notes))
        customer_id = cursor.lastrowid

        final_reference_id = reference_id_input if reference_id_input else f"CUST-{customer_id:06d}"
        try:
            cursor.execute("UPDATE customers SET ReferenceID = ? WHERE CustomerID = ?", (final_reference_id, customer_id))
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"Reference ID '{final_reference_id}' already exists for another customer.")

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_customers(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM customers"
    params = []
    if search_term:
        query += " WHERE CustomerName LIKE ? OR Email LIKE ? OR ReferenceID LIKE ? OR Phone LIKE ?" # Added Phone to search
        term = f"%{search_term}%"
        params.extend([term, term, term, term])
    query += " ORDER BY CustomerID DESC"
    cursor.execute(query, params)
    customers = cursor.fetchall()
    conn.close()
    return customers

def get_customer_by_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE CustomerID = ?", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return customer

def update_customer(cust_id, name, email, phone, reference_id_input, bill_addr, ship_addr, notes): # Added reference_id_input
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # If reference_id_input is empty, keep the old one or generate if it was null.
        # For simplicity, we assume app.py sends the current or new one.
        # If an empty string is passed for reference_id_input, it might try to set it to empty.
        # A better approach might be to fetch current_ref_id and only update if reference_id_input is not empty and different.
        # For now, direct update. Ensure app.py handles this carefully.
        if reference_id_input: # Only update if a new one is provided
            cursor.execute("UPDATE customers SET ReferenceID = ? WHERE CustomerID = ?", (reference_id_input, cust_id))

        cursor.execute('''
        UPDATE customers
        SET CustomerName = ?, Email = ?, Phone = ?, BillingAddress = ?, ShippingAddress = ?, Notes = ?
        WHERE CustomerID = ?
        ''', (name, email, phone, bill_addr, ship_addr, notes, cust_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"The new Reference ID '{reference_id_input}' might already be in use.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check for linked projects (ON DELETE SET NULL will handle this, but good for UI warning)
        # cursor.execute("SELECT 1 FROM projects WHERE CustomerID = ?", (customer_id,))
        # if cursor.fetchone():
        #     raise ValueError("Customer is associated with projects. Consider reassigning or deleting them first.")

        # Check for linked orders (ON DELETE SET NULL will handle this)
        # cursor.execute("SELECT 1 FROM orders WHERE CustomerID = ?", (customer_id,))
        # if cursor.fetchone():
        #     raise ValueError("Customer has existing orders. Consider reassigning or deleting them first.")

        # Check for linked invoices (ON DELETE RESTRICT will prevent deletion if invoices exist)
        cursor.execute("SELECT 1 FROM invoices WHERE CustomerID = ?", (customer_id,))
        if cursor.fetchone():
            raise ValueError("Customer has existing invoices. Cannot delete. Please resolve invoices first.")

        cursor.execute("DELETE FROM customers WHERE CustomerID = ?", (customer_id,))
        conn.commit()
    except sqlite3.IntegrityError as e: # Catch RESTRICT violation from Invoices
        conn.rollback()
        raise ValueError(f"Cannot delete customer (ID: {customer_id}). They have dependent records (e.g., Invoices). Details: {e}")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Supplier CRUD ---
def add_supplier(name, contact_person, email, phone, address):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO suppliers (SupplierName, ContactPerson, Email, Phone, Address)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, contact_person, email, phone, address))
        supplier_id = cursor.lastrowid
        reference_id = f"SUP-{supplier_id:06d}"
        cursor.execute("UPDATE suppliers SET ReferenceID = ? WHERE SupplierID = ?", (reference_id, supplier_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Supplier name '{name}' already exists.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_suppliers(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM suppliers"
    params = []
    if search_term:
        query += " WHERE SupplierName LIKE ? OR ContactPerson LIKE ? OR Email LIKE ? OR ReferenceID LIKE ?"
        term = f"%{search_term}%"
        params.extend([term, term, term, term])
    query += " ORDER BY SupplierName"
    cursor.execute(query, params)
    suppliers = cursor.fetchall()
    conn.close()
    return suppliers

def get_supplier_by_id(supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM suppliers WHERE SupplierID = ?", (supplier_id,))
    supplier = cursor.fetchone()
    conn.close()
    return supplier

def update_supplier(sup_id, name, contact_person, email, phone, address):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE suppliers
        SET SupplierName = ?, ContactPerson = ?, Email = ?, Phone = ?, Address = ?
        WHERE SupplierID = ?
        ''', (name, contact_person, email, phone, address, sup_id))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Supplier name '{name}' might already exist for another supplier.")
    finally:
        conn.close()


def delete_supplier(supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM suppliers WHERE SupplierID = ?", (supplier_id,))
        conn.commit()
    except Exception as e: # Could be IntegrityError if services use RESTRICT (they use CASCADE)
        conn.rollback()
        raise e
    finally:
        conn.close()


# --- Product CRUD ---
def add_product(name, sku, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        INSERT INTO products (ProductName, SKU, Description, Category, MaterialType, Dimensions, CostPrice, SellingPrice, QuantityInStock, ReorderLevel, SupplierID, ImagePath, LastStockUpdate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, sku, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path, last_update))
        product_id = cursor.lastrowid
        reference_id = sku if sku else f"PROD-{product_id:06d}"
        try:
            cursor.execute("UPDATE products SET ReferenceID = ? WHERE ProductID = ?", (reference_id, product_id))
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"Reference ID (from SKU or generated) '{reference_id}' already exists for another product.")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"SKU '{sku}' already exists, or other integrity error.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_products(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT p.*, s.SupplierName
    FROM products p
    LEFT JOIN suppliers s ON p.SupplierID = s.SupplierID
    """
    params = []
    if search_term:
        query += " WHERE (p.ProductName LIKE ? OR p.SKU LIKE ? OR p.ReferenceID LIKE ? OR p.Category LIKE ? OR s.SupplierName LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term])
    query += " ORDER BY p.ProductID DESC"
    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE ProductID = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def update_product(prod_id, name, sku, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        new_reference_id = sku if sku else f"PROD-{prod_id:06d}"
        cursor.execute('''
        UPDATE products
        SET ProductName = ?, SKU = ?, ReferenceID = ?, Description = ?, Category = ?, MaterialType = ?, Dimensions = ?,
            CostPrice = ?, SellingPrice = ?, QuantityInStock = ?, ReorderLevel = ?, SupplierID = ?,
            ImagePath = ?, LastStockUpdate = ?
        WHERE ProductID = ?
        ''', (name, sku, new_reference_id, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path, last_update, prod_id))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"New SKU '{sku}' or ReferenceID '{new_reference_id}' might already exist for another product.")
    finally:
        conn.close()


def update_product_stock(product_id, quantity_change):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET QuantityInStock = QuantityInStock + ?, LastStockUpdate = ? WHERE ProductID = ?",
                   (quantity_change, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        product = get_product_by_id(product_id)
        if product and product['ImagePath'] and os.path.exists(product['ImagePath']):
            try:
                os.remove(product['ImagePath'])
            except OSError as e:
                print(f"Error deleting image file {product['ImagePath']}: {e}")

        cursor.execute("DELETE FROM products WHERE ProductID = ?", (product_id,))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Cannot delete product (ID: {product_id}). It is referenced in order items or other dependent tables. Error: {e}")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Material CRUD ---
def add_material(name, material_type, unit, cost_unit, qty, supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        INSERT INTO materials (MaterialName, MaterialType, UnitOfMeasure, CostPerUnit, QuantityInStock, SupplierID, LastStockUpdate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, material_type, unit, cost_unit, qty, supplier_id, last_update))
        material_id = cursor.lastrowid
        reference_id = f"MAT-{material_id:06d}"
        cursor.execute("UPDATE materials SET ReferenceID = ? WHERE MaterialID = ?", (reference_id, material_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Material name '{name}' already exists.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_materials(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT m.*, s.SupplierName
    FROM materials m
    LEFT JOIN suppliers s ON m.SupplierID = s.SupplierID
    """
    params = []
    if search_term:
        query += " WHERE (m.MaterialName LIKE ? OR m.MaterialType LIKE ? OR s.SupplierName LIKE ? OR m.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term])
    query += " ORDER BY m.MaterialName"
    cursor.execute(query, params)
    materials = cursor.fetchall()
    conn.close()
    return materials

def get_material_by_id(material_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM materials WHERE MaterialID = ?", (material_id,))
    material = cursor.fetchone()
    conn.close()
    return material

def update_material(mat_id, name, material_type, unit, cost_unit, qty, supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        UPDATE materials
        SET MaterialName = ?, MaterialType = ?, UnitOfMeasure = ?, CostPerUnit = ?,
            QuantityInStock = ?, SupplierID = ?, LastStockUpdate = ?
        WHERE MaterialID = ?
        ''', (name, material_type, unit, cost_unit, qty, supplier_id, last_update, mat_id))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Material name '{name}' might already exist for another material.")
    finally:
        conn.close()


def delete_material(material_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materials WHERE MaterialID = ?", (material_id,))
    conn.commit()
    conn.close()

# --- Project CRUD ---
def add_project(name, customer_id, start_date, end_date, status, budget, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO projects (ProjectName, CustomerID, StartDate, EndDate, Status, Budget, Description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, customer_id, start_date, end_date, status, budget, description))
        project_id = cursor.lastrowid
        reference_id = f"PROJ-{project_id:06d}"
        cursor.execute("UPDATE projects SET ReferenceID = ? WHERE ProjectID = ?", (reference_id, project_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_projects(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT p.*, c.CustomerName, c.ReferenceID as CustomerRefID
    FROM projects p
    LEFT JOIN customers c ON p.CustomerID = c.CustomerID
    """
    params = []
    if search_term:
        query += " WHERE (p.ProjectName LIKE ? OR c.CustomerName LIKE ? OR c.ReferenceID LIKE ? OR p.Status LIKE ? OR p.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term])
    query += " ORDER BY p.ProjectID DESC"
    cursor.execute(query, params)
    projects = cursor.fetchall()
    conn.close()
    return projects

def get_project_by_id(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Join with customer to get CustomerName, useful if displaying project details
    cursor.execute("""
        SELECT p.*, c.CustomerName
        FROM projects p
        LEFT JOIN customers c ON p.CustomerID = c.CustomerID
        WHERE p.ProjectID = ?
    """, (project_id,))
    project = cursor.fetchone()
    conn.close()
    return project

def update_project(proj_id, name, customer_id, start_date, end_date, status, budget, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE projects
    SET ProjectName = ?, CustomerID = ?, StartDate = ?, EndDate = ?, Status = ?, Budget = ?, Description = ?
    WHERE ProjectID = ?
    ''', (name, customer_id, start_date, end_date, status, budget, description, proj_id))
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check for linked invoices (ON DELETE RESTRICT will prevent deletion)
        cursor.execute("SELECT 1 FROM invoices WHERE ProjectID = ?", (project_id,))
        if cursor.fetchone():
            raise ValueError("Project has existing invoices. Cannot delete. Please resolve invoices first.")

        # ON DELETE SET NULL handles orders/expenses/supplier_services linked
        cursor.execute("DELETE FROM projects WHERE ProjectID = ?", (project_id,))
        conn.commit()
    except sqlite3.IntegrityError as e: # Catch RESTRICT violation from Invoices
        conn.rollback()
        raise ValueError(f"Cannot delete project (ID: {project_id}). It has dependent records (e.g., Invoices). Details: {e}")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# --- Supplier Service CRUD ---
def add_supplier_service(supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    service_pk_id = None
    expense_logged_successfully = False
    try:
        cursor.execute('''
        INSERT INTO supplier_services (SupplierID, ProjectID, ServiceName, ServiceType, ServiceDate, Cost, ReceiptPath, Description, IsExpenseLogged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description))
        service_pk_id = cursor.lastrowid
        reference_id = f"SERV-{service_pk_id:06d}"
        cursor.execute("UPDATE supplier_services SET ReferenceID = ? WHERE ServiceID = ?", (reference_id, service_pk_id))

        if cost > 0 and service_pk_id:
            supplier = get_supplier_by_id(supplier_id)
            supplier_name_for_expense = supplier['SupplierName'] if supplier else f"Supplier ID: {supplier_id}"
            expense_desc = f"Service: {service_name} ({reference_id}) by {supplier_name_for_expense}"
            if service_type: expense_desc += f" ({service_type})"

            new_expense_pk_id = add_expense(
                exp_date=service_date, desc=expense_desc, category="Supplier Services", amount=cost,
                vendor=supplier_name_for_expense, project_id=project_id,
                receipt_ref=f"ServRef: {reference_id}" + (f", ReceiptFile: {os.path.basename(receipt_path)}" if receipt_path else ""),
                is_internal_call=True
            )
            if new_expense_pk_id:
                cursor.execute("UPDATE supplier_services SET IsExpenseLogged = 1 WHERE ServiceID = ?", (service_pk_id,))
                expense_logged_successfully = True
            else:
                print(f"Warning: Service (Ref: {reference_id}) added, but failed to auto-log expense.")
        conn.commit()
        return service_pk_id, expense_logged_successfully
    except Exception as e:
        conn.rollback()
        raise e
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
    if search_term:
        query += " WHERE (ss.ServiceName LIKE ? OR ss.ServiceType LIKE ? OR s.SupplierName LIKE ? OR p.ProjectName LIKE ? OR ss.Description LIKE ? OR ss.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term, term])
    query += " ORDER BY ss.ServiceDate DESC, ss.ServiceID DESC" # Added ServiceID for stable sort
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
    try:
        old_service_data = get_supplier_service_by_id(service_id)

        cursor.execute('''
        UPDATE supplier_services
        SET SupplierID = ?, ProjectID = ?, ServiceName = ?, ServiceType = ?, ServiceDate = ?,
            Cost = ?, ReceiptPath = ?, Description = ?
        WHERE ServiceID = ?
        ''', (supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description, service_id))

        if old_service_data and old_service_data['IsExpenseLogged'] and (old_service_data['Cost'] != cost or old_service_data['ServiceDate'] != service_date or old_service_data['ProjectID'] != project_id):
            # More sophisticated: find and update the linked expense, or delete and recreate.
            # For now, a stronger warning and advise manual check.
            print(f"CRITICAL WARNING in database.py: Service ID {service_id} (Ref: {old_service_data['ReferenceID']}) details (Cost, Date, or Project) changed. The associated auto-logged expense (ID: {old_service_data.get('ExpenseID_from_link', 'Unknown')}) REQUIRES MANUAL REVIEW AND ADJUSTMENT in the Expense Tracking module.")
            # To make this more robust, the supplier_services table could store the ExpenseID it generated.

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
        service_info = get_supplier_service_by_id(service_id)
        if service_info and service_info['ReceiptPath'] and os.path.exists(service_info['ReceiptPath']):
            try:
                os.remove(service_info['ReceiptPath'])
            except OSError as e:
                print(f"Error deleting receipt file {service_info['ReceiptPath']}: {e}")

        # If an expense was auto-logged, it should ideally be handled.
        # For now, app.py warns user to manually check.
        # A more advanced system might try to find and delete the linked expense if it was purely from this service.
        if service_info and service_info['IsExpenseLogged']:
            print(f"INFO: Service ID {service_id} (Ref: {service_info['ReferenceID']}) is being deleted. The associated auto-logged expense may need to be manually reviewed or deleted from Expense Tracking.")

        cursor.execute("DELETE FROM supplier_services WHERE ServiceID = ?", (service_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Order & Order Item CRUD ---
def add_order(order_date, customer_id, project_id, status, total_amount, payment_status, ship_addr, notes, reference_id_input=None): # Added reference_id_input
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO orders (OrderDate, CustomerID, ProjectID, OrderStatus, TotalAmount, PaymentStatus, ShippingAddress, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_date, customer_id, project_id, status, total_amount, payment_status, ship_addr, notes))
        order_id = cursor.lastrowid

        final_reference_id = reference_id_input if reference_id_input else f"ORD-{order_id:06d}"
        try:
            cursor.execute("UPDATE orders SET ReferenceID = ? WHERE OrderID = ?", (final_reference_id, order_id))
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"Reference ID '{final_reference_id}' already exists for another order.")

        conn.commit()
        return order_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def add_order_item(order_id, product_id, quantity, unit_price, discount):
    conn = get_db_connection()
    cursor = conn.cursor()
    line_total = (float(unit_price) * int(quantity)) - float(discount)
    cursor.execute('''
    INSERT INTO order_items (OrderID, ProductID, QuantitySold, UnitPriceAtSale, Discount, LineTotal)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (order_id, product_id, quantity, unit_price, discount, line_total))
    conn.commit()
    conn.close()

def get_all_orders(search_term="", limit=None): # Added limit
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT o.*, c.CustomerName, c.ReferenceID AS CustomerRefID, pr.ProjectName, pr.ReferenceID AS ProjectRefID
    FROM orders o
    LEFT JOIN customers c ON o.CustomerID = c.CustomerID
    LEFT JOIN projects pr ON o.ProjectID = pr.ProjectID
    """
    params = []
    if search_term:
        query += " WHERE (o.ReferenceID LIKE ? OR c.CustomerName LIKE ? OR c.ReferenceID LIKE ? OR pr.ProjectName LIKE ? OR pr.ReferenceID LIKE ? OR o.OrderStatus LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term, term])
    query += " ORDER BY o.OrderDate DESC, o.OrderID DESC" # Added OrderID for stable sort
    if limit:
        query += f" LIMIT {int(limit)}" # Be cautious with direct int insertion if limit isn't controlled
    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_order_by_id(order_id): # New function
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT o.*, c.CustomerName, pr.ProjectName
    FROM orders o
    LEFT JOIN customers c ON o.CustomerID = c.CustomerID
    LEFT JOIN projects pr ON o.ProjectID = pr.ProjectID
    WHERE o.OrderID = ?
    """, (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order

def update_order_basic_info(order_id, order_date, customer_id, project_id, status, payment_status, ship_addr, notes, reference_id_input): # New function
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if reference_id_input: # Only update if a new one is provided and not empty
            cursor.execute("UPDATE orders SET ReferenceID = ? WHERE OrderID = ?", (reference_id_input, order_id))

        cursor.execute('''
        UPDATE orders
        SET OrderDate = ?, CustomerID = ?, ProjectID = ?, OrderStatus = ?,
            PaymentStatus = ?, ShippingAddress = ?, Notes = ?
        WHERE OrderID = ?
        ''', (order_date, customer_id, project_id, status, payment_status, ship_addr, notes, order_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"The new Reference ID '{reference_id_input}' might already be in use for another order.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_orders_by_customer_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT o.*, pr.ProjectName, o.ReferenceID as OrderReferenceID, pr.ReferenceID as ProjectRefID
    FROM orders o
    LEFT JOIN projects pr ON o.ProjectID = pr.ProjectID
    WHERE o.CustomerID = ?
    ORDER BY o.OrderDate DESC
    ''', (customer_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_order_items_by_order_id(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT oi.*, p.ProductName, p.SKU as ProductSKU, p.ReferenceID as ProductRefID
    FROM order_items oi
    JOIN products p ON oi.ProductID = p.ProductID
    WHERE oi.OrderID = ?
    ''', (order_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def update_order_total(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(LineTotal) FROM order_items WHERE OrderID = ?", (order_id,))
    total_amount_tuple = cursor.fetchone()
    total_amount = total_amount_tuple[0] if total_amount_tuple and total_amount_tuple[0] is not None else 0
    cursor.execute("UPDATE orders SET TotalAmount = ? WHERE OrderID = ?", (total_amount, order_id))
    conn.commit()
    conn.close()


# --- Expense CRUD ---
def add_expense(exp_date, desc, category, amount, vendor, project_id, receipt_ref, is_internal_call=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    expense_pk_id = None
    try:
        cursor.execute('''
        INSERT INTO expenses (ExpenseDate, Description, Category, Amount, Vendor, ProjectID, ReceiptReference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (exp_date, desc, category, amount, vendor, project_id, receipt_ref))
        expense_pk_id = cursor.lastrowid
        reference_id = f"EXP-{expense_pk_id:06d}"
        cursor.execute("UPDATE expenses SET ReferenceID = ? WHERE ExpenseID = ?", (reference_id, expense_pk_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        if not is_internal_call:
            raise e
        else:
            print(f"INTERNAL ERROR during add_expense for '{desc}': {e}")
            return None
    finally:
        conn.close()
    return expense_pk_id


def get_all_expenses(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT e.*, p.ProjectName, p.ReferenceID as ProjectRefID
    FROM expenses e
    LEFT JOIN projects p ON e.ProjectID = p.ProjectID
    """
    params = []
    if search_term:
        query += " WHERE (e.Description LIKE ? OR e.Category LIKE ? OR e.Vendor LIKE ? OR p.ProjectName LIKE ? OR p.ReferenceID LIKE ? OR e.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term, term])
    query += " ORDER BY e.ExpenseDate DESC, e.ExpenseID DESC" # Added ExpenseID for stable sort
    cursor.execute(query, params)
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def get_expenses_by_project_id(project_id): # New for reports
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT e.*
    FROM expenses e
    WHERE e.ProjectID = ?
    ORDER BY e.ExpenseDate DESC
    ''', (project_id,))
    expenses = cursor.fetchall()
    conn.close()
    return expenses

# --- Invoice CRUD (New) ---
def get_next_invoice_reference_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    # This is a simple way, could be more robust (e.g., find max number for current year)
    # For a more robust sequence like INV-YYYY-NNN:
    # 1. Get current year
    # 2. Query max InvoiceReferenceID for that year (e.g., SELECT MAX(InvoiceReferenceID) FROM invoices WHERE InvoiceReferenceID LIKE 'INV-YYYY-%')
    # 3. Parse out the NNN part, increment, and format.
    # For simplicity, this just provides a basic template.
    year = datetime.now().year
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE InvoiceReferenceID LIKE ?", (f"INV-{year}-%",))
    count = cursor.fetchone()[0]
    conn.close()
    return f"INV-{year}-{count + 1:04d}"


def add_invoice(invoice_reference_id, project_id, customer_id, issue_date, due_date, payment_date, total_amount, status, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO invoices (InvoiceReferenceID, ProjectID, CustomerID, IssueDate, DueDate, PaymentDate, TotalAmount, Status, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (invoice_reference_id, project_id, customer_id, issue_date, due_date, payment_date, total_amount, status, notes))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE constraint failed: invoices.InvoiceReferenceID" in str(e):
            raise ValueError(f"Invoice Reference ID '{invoice_reference_id}' already exists.")
        raise e # Re-raise other integrity errors
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_invoices(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT i.*, p.ProjectName, p.ReferenceID as ProjectRefID, c.CustomerName, c.ReferenceID as CustomerRefID
    FROM invoices i
    JOIN projects p ON i.ProjectID = p.ProjectID
    JOIN customers c ON i.CustomerID = c.CustomerID
    """
    params = []
    if search_term:
        query += " WHERE (i.InvoiceReferenceID LIKE ? OR p.ProjectName LIKE ? OR c.CustomerName LIKE ? OR i.Status LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term])
    query += " ORDER BY i.IssueDate DESC, i.InvoiceID DESC"
    cursor.execute(query, params)
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_invoice_by_id(invoice_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.*, p.ProjectName, c.CustomerName
    FROM invoices i
    JOIN projects p ON i.ProjectID = p.ProjectID
    JOIN customers c ON i.CustomerID = c.CustomerID
    WHERE i.InvoiceID = ?
    """, (invoice_id,))
    invoice = cursor.fetchone()
    conn.close()
    return invoice

def update_invoice(invoice_id, invoice_reference_id, project_id, customer_id, issue_date, due_date, payment_date, total_amount, status, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE invoices
        SET InvoiceReferenceID = ?, ProjectID = ?, CustomerID = ?, IssueDate = ?, DueDate = ?,
            PaymentDate = ?, TotalAmount = ?, Status = ?, Notes = ?
        WHERE InvoiceID = ?
        ''', (invoice_reference_id, project_id, customer_id, issue_date, due_date, payment_date, total_amount, status, notes, invoice_id))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE constraint failed: invoices.InvoiceReferenceID" in str(e):
            raise ValueError(f"Invoice Reference ID '{invoice_reference_id}' already exists for another invoice.")
        raise e
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_invoice(invoice_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM invoices WHERE InvoiceID = ?", (invoice_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_invoices_by_customer_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT i.*, p.ProjectName, p.ReferenceID as ProjectRefID
    FROM invoices i
    JOIN projects p ON i.ProjectID = p.ProjectID
    WHERE i.CustomerID = ?
    ORDER BY i.IssueDate DESC
    ''', (customer_id,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_invoices_by_project_id(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT i.*, c.CustomerName
    FROM invoices i
    JOIN customers c ON i.CustomerID = c.CustomerID
    WHERE i.ProjectID = ?
    ORDER BY i.IssueDate DESC
    ''', (project_id,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

# --- Functions for Customer Detail Page ---
def get_projects_by_customer_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.*
    FROM projects p
    WHERE p.CustomerID = ?
    ORDER BY p.StartDate DESC, p.ProjectID DESC
    ''', (customer_id,))
    projects = cursor.fetchall()
    conn.close()
    return projects


# --- Helper ---
def rows_to_dicts(rows):
    if rows is None: return []
    return [dict(row) for row in rows]

init_db()
