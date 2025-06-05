--- START OF FILE database.py ---

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
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def column_exists(cursor, table_name, column_name):
    """Checks if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Customers
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
    if not column_exists(cursor, "customers", "ReferenceID"):
        cursor.execute("ALTER TABLE customers ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to customers table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_ReferenceID ON customers (ReferenceID)")
        # print("INFO: Ensured UNIQUE index idx_customers_ReferenceID exists on customers.ReferenceID.")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on customers.ReferenceID. Data might not be unique or column might not allow UNIQUE for existing NULLs if DB treats them non-distinctly for index. Error: {e}")


    # Suppliers
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
    if not column_exists(cursor, "suppliers", "ReferenceID"):
        cursor.execute("ALTER TABLE suppliers ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to suppliers table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_ReferenceID ON suppliers (ReferenceID)")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on suppliers.ReferenceID. Error: {e}")

    # Products
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
    if not column_exists(cursor, "products", "ReferenceID"):
        cursor.execute("ALTER TABLE products ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to products table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_ReferenceID ON products (ReferenceID)")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on products.ReferenceID. Error: {e}")


    # Materials
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
    if not column_exists(cursor, "materials", "ReferenceID"):
        cursor.execute("ALTER TABLE materials ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to materials table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_materials_ReferenceID ON materials (ReferenceID)")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on materials.ReferenceID. Error: {e}")

    # Projects
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectName TEXT NOT NULL,
        StartDate TEXT,
        EndDate TEXT,
        Status TEXT,
        Budget REAL,
        Description TEXT
    )
    ''')
    if not column_exists(cursor, "projects", "ReferenceID"):
        cursor.execute("ALTER TABLE projects ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to projects table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_ReferenceID ON projects (ReferenceID)")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on projects.ReferenceID. Error: {e}")

    if not column_exists(cursor, "projects", "CustomerID"):
        cursor.execute("ALTER TABLE projects ADD COLUMN CustomerID INTEGER REFERENCES customers(CustomerID) ON DELETE SET NULL")
        print("INFO: Added CustomerID column to projects table.")

    # Supplier Services
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
    if not column_exists(cursor, "supplier_services", "ReferenceID"):
        cursor.execute("ALTER TABLE supplier_services ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to supplier_services table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_services_ReferenceID ON supplier_services (ReferenceID)")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on supplier_services.ReferenceID. Error: {e}")


    # Orders
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
    if not column_exists(cursor, "orders", "ReferenceID"):
        cursor.execute("ALTER TABLE orders ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to orders table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_ReferenceID ON orders (ReferenceID)")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on orders.ReferenceID. Error: {e}")


    # Expenses
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
    if not column_exists(cursor, "expenses", "ReferenceID"):
        cursor.execute("ALTER TABLE expenses ADD COLUMN ReferenceID TEXT")
        print("INFO: Added ReferenceID column to expenses table.")
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_expenses_ReferenceID ON expenses (ReferenceID)")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on expenses.ReferenceID. Error: {e}")

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

    # Invoices
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
        Status TEXT NOT NULL,
        Notes TEXT,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE RESTRICT,
        FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID) ON DELETE RESTRICT
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

        final_reference_id = reference_id_input if reference_id_input and reference_id_input.strip() else f"CUST-{customer_id:06d}"
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
        query += " WHERE CustomerName LIKE ? OR Email LIKE ? OR ReferenceID LIKE ? OR Phone LIKE ?"
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

def update_customer(cust_id, name, email, phone, reference_id_input, bill_addr, ship_addr, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        current_customer_row = get_customer_by_id(cust_id)
        if not current_customer_row:
            raise ValueError(f"Customer with ID {cust_id} not found.")
        current_customer = dict(current_customer_row)

        final_reference_id = current_customer.get('ReferenceID') # Default to current
        if reference_id_input and reference_id_input.strip() and reference_id_input.strip() != current_customer.get('ReferenceID'):
            final_reference_id = reference_id_input.strip()
        elif not current_customer.get('ReferenceID') and reference_id_input and reference_id_input.strip():
            final_reference_id = reference_id_input.strip()
        elif not current_customer.get('ReferenceID') and not (reference_id_input and reference_id_input.strip()):
             final_reference_id = f"CUST-{cust_id:06d}"

        cursor.execute('''
        UPDATE customers
        SET CustomerName = ?, Email = ?, Phone = ?, ReferenceID = ?, BillingAddress = ?, ShippingAddress = ?, Notes = ?
        WHERE CustomerID = ?
        ''', (name, email, phone, final_reference_id, bill_addr, ship_addr, notes, cust_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"The new Reference ID '{final_reference_id}' might already be in use.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM invoices WHERE CustomerID = ?", (customer_id,))
        if cursor.fetchone():
            raise ValueError("Customer has existing invoices. Cannot delete. Please resolve invoices first.")

        cursor.execute("DELETE FROM customers WHERE CustomerID = ?", (customer_id,))
        conn.commit()
    except sqlite3.IntegrityError as e:
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
        conn.rollback()
        raise ValueError(f"Supplier name '{name}' might already exist for another supplier.")
    except Exception as e:
        conn.rollback()
        raise e
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
        product_id = cursor.lastrowid
        reference_id = sku if sku and sku.strip() else f"PROD-{product_id:06d}"
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
        new_reference_id = sku if sku and sku.strip() else f"PROD-{prod_id:06d}"
        cursor.execute('''
        UPDATE products
        SET ProductName = ?, SKU = ?, ReferenceID = ?, Description = ?, Category = ?, MaterialType = ?, Dimensions = ?,
            CostPrice = ?, SellingPrice = ?, QuantityInStock = ?, ReorderLevel = ?, SupplierID = ?,
            ImagePath = ?, LastStockUpdate = ?
        WHERE ProductID = ?
        ''', (name, sku, new_reference_id, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path, last_update, prod_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"New SKU '{sku}' or ReferenceID '{new_reference_id}' might already exist for another product.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_product_stock(product_id, quantity_change):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE products SET QuantityInStock = QuantityInStock + ?, LastStockUpdate = ? WHERE ProductID = ?",
                       (quantity_change, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), product_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        product_row = get_product_by_id(product_id)
        if product_row:
            product = dict(product_row)
            if product.get('ImagePath') and os.path.exists(product['ImagePath']):
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
        conn.rollback()
        raise ValueError(f"Material name '{name}' might already exist for another material.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_material(material_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM materials WHERE MaterialID = ?", (material_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
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
    try:
        cursor.execute('''
        UPDATE projects
        SET ProjectName = ?, CustomerID = ?, StartDate = ?, EndDate = ?, Status = ?, Budget = ?, Description = ?
        WHERE ProjectID = ?
        ''', (name, customer_id, start_date, end_date, status, budget, description, proj_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM invoices WHERE ProjectID = ?", (project_id,))
        if cursor.fetchone():
            raise ValueError("Project has existing invoices. Cannot delete. Please resolve invoices first.")
        cursor.execute("DELETE FROM projects WHERE ProjectID = ?", (project_id,))
        conn.commit()
    except sqlite3.IntegrityError as e:
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
            supplier_row = get_supplier_by_id(supplier_id)
            supplier_name_for_expense = dict(supplier_row)['SupplierName'] if supplier_row else f"Supplier ID: {supplier_id}"
            
            expense_desc = f"Service: {service_name} ({reference_id}) by {supplier_name_for_expense}"
            if service_type: expense_desc += f" ({service_type})"

            new_expense_pk_id = add_expense(
                exp_date=service_date, desc=expense_desc, category="Supplier Services", amount=cost,
                vendor=supplier_name_for_expense, project_id=project_id,
                receipt_ref=f"ServRef: {reference_id}" + (f", ReceiptFile: {os.path.basename(receipt_path)}" if receipt_path and os.path.exists(receipt_path) else ""), # Check receipt_path
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
    query += " ORDER BY ss.ServiceDate DESC, ss.ServiceID DESC"
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

def update_supplier_service(service_id, supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description, is_expense_logged_param):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        old_service_data_row = get_supplier_service_by_id(service_id)
        old_service_data = dict(old_service_data_row) if old_service_data_row else None

        cursor.execute('''
        UPDATE supplier_services
        SET SupplierID = ?, ProjectID = ?, ServiceName = ?, ServiceType = ?, ServiceDate = ?,
            Cost = ?, ReceiptPath = ?, Description = ?, IsExpenseLogged = ?
        WHERE ServiceID = ?
        ''', (supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description, 1 if is_expense_logged_param else 0, service_id))

        if old_service_data and old_service_data.get('IsExpenseLogged'): # Use .get for safety
            cost_changed = old_service_data.get('Cost') != cost
            date_changed = old_service_data.get('ServiceDate') != service_date
            # ... other checks ...
            if cost_changed or date_changed: # Add other conditions as needed
                 print(f"WARNING in database.py update_supplier_service: Service ID {service_id} details changed. Associated auto-logged expense might need manual review.")
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
        service_info_row = get_supplier_service_by_id(service_id)
        if service_info_row:
            service_info = dict(service_info_row)
            if service_info.get('ReceiptPath') and os.path.exists(service_info['ReceiptPath']):
                try:
                    os.remove(service_info['ReceiptPath'])
                except OSError as e:
                    print(f"Error deleting receipt file {service_info['ReceiptPath']}: {e}")

            if service_info.get('IsExpenseLogged'):
                print(f"INFO: Service ID {service_id} (Ref: {service_info.get('ReferenceID', 'N/A')}) is being deleted. The associated auto-logged expense may need manual review.")

        cursor.execute("DELETE FROM supplier_services WHERE ServiceID = ?", (service_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Order & Order Item CRUD ---
def add_order(order_date, customer_id, project_id, status, total_amount, payment_status, ship_addr, notes, reference_id_input=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO orders (OrderDate, CustomerID, ProjectID, OrderStatus, TotalAmount, PaymentStatus, ShippingAddress, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_date, customer_id, project_id, status, total_amount, payment_status, ship_addr, notes))
        order_id = cursor.lastrowid

        final_reference_id = reference_id_input if reference_id_input and reference_id_input.strip() else f"ORD-{order_id:06d}"
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
    try:
        line_total = (float(unit_price) * int(quantity)) - float(discount)
        cursor.execute('''
        INSERT INTO order_items (OrderID, ProductID, QuantitySold, UnitPriceAtSale, Discount, LineTotal)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, product_id, quantity, unit_price, discount, line_total))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_orders(search_term="", limit=None):
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
    query += " ORDER BY o.OrderDate DESC, o.OrderID DESC"
    if limit and isinstance(limit, int) and limit > 0:
        query += f" LIMIT {limit}"
    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_order_by_id(order_id):
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

def update_order_basic_info(order_id, order_date, customer_id, project_id, status, payment_status, ship_addr, notes, reference_id_input):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        current_order_row = get_order_by_id(order_id)
        if not current_order_row:
            raise ValueError(f"Order with ID {order_id} not found.")
        current_order = dict(current_order_row)


        final_reference_id = current_order.get('ReferenceID')
        if reference_id_input and reference_id_input.strip() and reference_id_input.strip() != current_order.get('ReferenceID'):
            final_reference_id = reference_id_input.strip()
        elif not current_order.get('ReferenceID') and reference_id_input and reference_id_input.strip():
            final_reference_id = reference_id_input.strip()
        elif not current_order.get('ReferenceID') and not (reference_id_input and reference_id_input.strip()):
             final_reference_id = f"ORD-{order_id:06d}"


        cursor.execute('''
        UPDATE orders
        SET OrderDate = ?, CustomerID = ?, ProjectID = ?, OrderStatus = ?, ReferenceID = ?,
            PaymentStatus = ?, ShippingAddress = ?, Notes = ?
        WHERE OrderID = ?
        ''', (order_date, customer_id, project_id, status, final_reference_id, payment_status, ship_addr, notes, order_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"The new Reference ID '{final_reference_id}' might already be in use for another order.")
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
    try:
        cursor.execute("SELECT SUM(LineTotal) FROM order_items WHERE OrderID = ?", (order_id,))
        total_amount_tuple = cursor.fetchone()
        total_amount = total_amount_tuple[0] if total_amount_tuple and total_amount_tuple[0] is not None else 0
        cursor.execute("UPDATE orders SET TotalAmount = ? WHERE OrderID = ?", (total_amount, order_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
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
            print(f"INTERNAL ERROR during add_expense (desc: '{desc}', amount: {amount}): {e}")
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
    query += " ORDER BY e.ExpenseDate DESC, e.ExpenseID DESC"
    cursor.execute(query, params)
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def get_expenses_by_project_id(project_id):
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

# --- Invoice CRUD ---
def get_next_invoice_reference_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    year_month = datetime.now().strftime("%Y%m")
    like_pattern = f"INV-{year_month}-%"
    
    cursor.execute("SELECT MAX(InvoiceReferenceID) FROM invoices WHERE InvoiceReferenceID LIKE ?", (like_pattern,))
    max_ref_row = cursor.fetchone()
    max_ref = max_ref_row[0] if max_ref_row else None
    
    next_num = 1
    if max_ref:
        try:
            last_num_str = max_ref.split('-')[-1]
            next_num = int(last_num_str) + 1
        except (IndexError, ValueError):
            # Fallback if parsing fails, count existing for the month as a rough estimate
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE InvoiceReferenceID LIKE ?", (like_pattern,))
            count_row = cursor.fetchone()
            next_num = (count_row[0] if count_row else 0) + 1
    conn.close()
    return f"INV-{year_month}-{next_num:04d}"


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
        # Check for other foreign key violations if needed
        # elif "FOREIGN KEY constraint failed" in str(e):
        #     # Determine which FK failed if possible, or generic message
        #     raise ValueError(f"Invalid ProjectID or CustomerID provided for the invoice. Details: {e}")
        raise e
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
        query += " WHERE (i.InvoiceReferenceID LIKE ? OR p.ProjectName LIKE ? OR c.CustomerName LIKE ? OR i.Status LIKE ? OR c.ReferenceID LIKE ? OR p.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term, term])
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
    if not rows:
        return []
    if isinstance(rows[0], dict): # Check if already list of dicts
        return rows
    if isinstance(rows[0], sqlite3.Row): # Check if list of sqlite3.Row
        return [dict(row) for row in rows]
    # If it's a single sqlite3.Row (though functions usually return lists or None for single item)
    # This case is less likely given the typical usage pattern.
    # Consider if single item fetches should return dict directly or None.
    # For now, assume 'rows' is a list or None.
    return [] # Fallback for unexpected type

# Call init_db() once when the module is imported.
init_db()
