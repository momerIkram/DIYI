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
    conn = sqlite3.connect(DATABASE_NAME, timeout=10) # Added timeout
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Core Entities ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
        CustomerName TEXT NOT NULL,
        Email TEXT,
        Phone TEXT,
        BillingAddress TEXT,
        ShippingAddress TEXT,
        RegistrationDate TEXT,
        Notes TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
        SupplierName TEXT NOT NULL UNIQUE,
        ContactPerson TEXT,
        Email TEXT,
        Phone TEXT,
        Address TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        MaterialID INTEGER PRIMARY KEY AUTOINCREMENT,
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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # --- Supplier Services Table ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS supplier_services (
        ServiceID INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # --- Transactional Entities ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        ExpenseID INTEGER PRIMARY KEY AUTOINCREMENT,
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

    conn.commit()
    conn.close()


# --- Customer CRUD ---
def add_customer(name, email, phone, bill_addr, ship_addr, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
    INSERT INTO customers (CustomerName, Email, Phone, BillingAddress, ShippingAddress, RegistrationDate, Notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, bill_addr, ship_addr or bill_addr, reg_date, notes))
    conn.commit()
    conn.close()

def get_all_customers(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM customers"
    params = []
    if search_term:
        query += " WHERE CustomerName LIKE ? OR Email LIKE ?"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    query += " ORDER BY CustomerName"
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

def update_customer(cust_id, name, email, phone, bill_addr, ship_addr, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE customers
    SET CustomerName = ?, Email = ?, Phone = ?, BillingAddress = ?, ShippingAddress = ?, Notes = ?
    WHERE CustomerID = ?
    ''', (name, email, phone, bill_addr, ship_addr, notes, cust_id))
    conn.commit()
    conn.close()

def delete_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM projects WHERE CustomerID = ?", (customer_id,))
        if cursor.fetchone():
            raise ValueError("Customer is associated with projects. Cannot delete.")
        cursor.execute("SELECT 1 FROM orders WHERE CustomerID = ?", (customer_id,))
        if cursor.fetchone():
            raise ValueError("Customer has existing orders. Cannot delete.")
        
        cursor.execute("DELETE FROM customers WHERE CustomerID = ?", (customer_id,))
        conn.commit()
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
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Supplier name '{name}' already exists.")
    finally:
        conn.close()

def get_all_suppliers(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM suppliers"
    params = []
    if search_term:
        query += " WHERE SupplierName LIKE ? OR ContactPerson LIKE ? OR Email LIKE ?"
        params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
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
    except Exception as e:
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
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"SKU '{sku}' already exists.")
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
        query += " WHERE (p.ProductName LIKE ? OR p.SKU LIKE ? OR p.Category LIKE ? OR s.SupplierName LIKE ?)" # Ensure search covers supplier name
        term = f"%{search_term}%"
        params.extend([term, term, term, term])
    query += " ORDER BY p.ProductName"
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
        cursor.execute('''
        UPDATE products
        SET ProductName = ?, SKU = ?, Description = ?, Category = ?, MaterialType = ?, Dimensions = ?,
            CostPrice = ?, SellingPrice = ?, QuantityInStock = ?, ReorderLevel = ?, SupplierID = ?,
            ImagePath = ?, LastStockUpdate = ?
        WHERE ProductID = ?
        ''', (name, sku, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path, last_update, prod_id))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"SKU '{sku}' might already exist for another product.")
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
        raise ValueError(f"Cannot delete product (ID: {product_id}). It is referenced in order items. Error: {e}")
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
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Material name '{name}' already exists.")
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
        query += " WHERE (m.MaterialName LIKE ? OR m.MaterialType LIKE ? OR s.SupplierName LIKE ?)" # Ensure supplier name included
        term = f"%{search_term}%"
        params.extend([term, term, term])
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
    cursor.execute('''
    INSERT INTO projects (ProjectName, CustomerID, StartDate, EndDate, Status, Budget, Description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, customer_id, start_date, end_date, status, budget, description))
    conn.commit()
    conn.close()

def get_all_projects(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT p.*, c.CustomerName
    FROM projects p
    LEFT JOIN customers c ON p.CustomerID = c.CustomerID
    """
    params = []
    if search_term:
        query += " WHERE (p.ProjectName LIKE ? OR c.CustomerName LIKE ? OR p.Status LIKE ?)" # Customer name in search
        term = f"%{search_term}%"
        params.extend([term, term, term])
    query += " ORDER BY p.ProjectName"
    cursor.execute(query, params)
    projects = cursor.fetchall()
    conn.close()
    return projects

def get_project_by_id(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE ProjectID = ?", (project_id,))
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
        cursor.execute("DELETE FROM projects WHERE ProjectID = ?", (project_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
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
        
        if cost > 0 and service_id:
            supplier = get_supplier_by_id(supplier_id) 
            supplier_name_for_expense = supplier['SupplierName'] if supplier else f"Supplier ID: {supplier_id}"
            expense_desc = f"Service: {service_name} by {supplier_name_for_expense}"
            if service_type: expense_desc += f" ({service_type})"

            new_expense_id = add_expense(
                exp_date=service_date, desc=expense_desc, category="Supplier Services", amount=cost,
                vendor=supplier_name_for_expense, project_id=project_id,
                receipt_ref=f"Service ID: {service_id}" + (f", Receipt: {os.path.basename(receipt_path)}" if receipt_path else ""),
                is_internal_call=True
            )
            if new_expense_id:
                cursor.execute("UPDATE supplier_services SET IsExpenseLogged = 1 WHERE ServiceID = ?", (service_id,))
                expense_logged_successfully = True
            else:
                print(f"Warning: Service ID {service_id} added, but failed to auto-log expense.")      
        conn.commit()
        return service_id, expense_logged_successfully
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
    try:
        # Get old service data for comparison or potential complex update logic for expenses
        old_service_data = get_supplier_service_by_id(service_id)
        
        cursor.execute('''
        UPDATE supplier_services
        SET SupplierID = ?, ProjectID = ?, ServiceName = ?, ServiceType = ?, ServiceDate = ?,
            Cost = ?, ReceiptPath = ?, Description = ? 
        WHERE ServiceID = ?
        ''', (supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description, service_id))
        
        # More robust: if cost/date/supplier changes, might need to adjust or recreate the associated expense.
        # This is a complex part of system design (transaction immutability vs. editability).
        # For now, a simple warning if cost changes after being logged is better than silent data mismatch.
        if old_service_data and old_service_data['IsExpenseLogged'] and old_service_data['Cost'] != cost:
            print(f"WARNING in database.py: Service ID {service_id} cost was changed from {old_service_data['Cost']} to {cost} after expense was logged. Associated expense might need manual adjustment.")
            # This print will go to server logs if deployed on Streamlit Cloud. A UI warning in app.py is better.

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
        
        cursor.execute("DELETE FROM supplier_services WHERE ServiceID = ?", (service_id,))
        # Note: Does not automatically delete the associated expense record. This might need manual attention or a more direct link.
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Order & Order Item CRUD ---
def add_order(order_date, customer_id, project_id, status, total_amount, payment_status, ship_addr, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO orders (OrderDate, CustomerID, ProjectID, OrderStatus, TotalAmount, PaymentStatus, ShippingAddress, Notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_date, customer_id, project_id, status, total_amount, payment_status, ship_addr, notes))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

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

def get_all_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT o.*, c.CustomerName, pr.ProjectName
    FROM orders o
    LEFT JOIN customers c ON o.CustomerID = c.CustomerID
    LEFT JOIN projects pr ON o.ProjectID = pr.ProjectID
    ORDER BY o.OrderDate DESC
    ''')
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_order_items_by_order_id(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT oi.*, p.ProductName
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
    total_amount = total_amount_tuple[0] if total_amount_tuple and total_amount_tuple[0] is not None else 0 # Handle if no items
    cursor.execute("UPDATE orders SET TotalAmount = ? WHERE OrderID = ?", (total_amount, order_id))
    conn.commit()
    conn.close()


# --- Expense CRUD ---
def add_expense(exp_date, desc, category, amount, vendor, project_id, receipt_ref, is_internal_call=False): # is_internal_call added
    conn = get_db_connection()
    cursor = conn.cursor()
    expense_id = None # Initialize
    try:
        cursor.execute('''
        INSERT INTO expenses (ExpenseDate, Description, Category, Amount, Vendor, ProjectID, ReceiptReference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (exp_date, desc, category, amount, vendor, project_id, receipt_ref))
        expense_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        if not is_internal_call:
            raise e
        else:
            print(f"INTERNAL ERROR during add_expense for '{desc}': {e}") # Log, don't break internal process
    finally:
        conn.close()
    return expense_id # Return ID or None if internal call failed


def get_all_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT e.*, p.ProjectName
    FROM expenses e
    LEFT JOIN projects p ON e.ProjectID = p.ProjectID
    ORDER BY e.ExpenseDate DESC
    ''')
    expenses = cursor.fetchall()
    conn.close()
    return expenses

# --- Helper to convert SQLite Row objects to list of dicts ---
def rows_to_dicts(rows):
    if rows is None: return [] # Handle if None is passed
    return [dict(row) for row in rows]

# Initialize the database and tables
init_db()
