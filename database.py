

import sqlite3
import os
from datetime import datetime

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Get directory of this file
DATABASE_DIR = os.path.join(BASE_DIR, "data")
DATABASE_NAME = os.path.join(DATABASE_DIR, "furniture_management.db")
IMAGE_DIR = os.path.join(BASE_DIR, "images") # For product images
RECEIPT_DIR = os.path.join(DATABASE_DIR, "receipts") # For supplier service receipts

if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
    print(f"INFO: Created directory {DATABASE_DIR}")
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
    print(f"INFO: Created directory {IMAGE_DIR}")
if not os.path.exists(RECEIPT_DIR):
    os.makedirs(RECEIPT_DIR)
    print(f"INFO: Created directory {RECEIPT_DIR}")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _table_exists(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def _column_exists(cursor, table_name, column_name):
    if not _table_exists(cursor, table_name):
        return False
    cursor.execute(f"PRAGMA table_info({table_name.lower()})") # Ensure lowercase for table name if DB is case sensitive in schema queries
    columns = [info['name'] for info in cursor.fetchall()]
    return column_name in columns

def _add_column_if_not_exists(cursor, table_name, column_name, column_type):
    if not _column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            print(f"INFO: Added column '{column_name}' to table '{table_name}'.")
        except sqlite3.Error as e:
            print(f"WARNING: Error adding column {column_name} to {table_name}: {e}")

def _ensure_unique_index(cursor, table_name, column_name):
    index_name = f"idx_{table_name}_{column_name}"
    try:
        # For TEXT columns that might store empty strings instead of NULLs for uniqueness
        # A better approach is to ensure empty strings are stored as NULL if ReferenceID is optional.
        # For now, this tries to create it. If it fails due to non-unique NULLs (some DBs),
        # or actual duplicate values, it will print a warning.
        cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})")
        # print(f"INFO: Ensured UNIQUE index {index_name} exists on {table_name}.{column_name}.")
    except sqlite3.OperationalError as e:
        print(f"WARNING: Could not create UNIQUE index on {table_name}.{column_name}. Data might not be unique or column has problematic NULLs/empty strings. Error: {e}")


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
        Notes TEXT,
        ReferenceID TEXT 
    )
    ''')
    _add_column_if_not_exists(cursor, "customers", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "customers", "ReferenceID")

    # Suppliers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
        SupplierName TEXT NOT NULL UNIQUE,
        ContactPerson TEXT,
        Email TEXT,
        Phone TEXT,
        Address TEXT,
        ReferenceID TEXT
    )
    ''')
    _add_column_if_not_exists(cursor, "suppliers", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "suppliers", "ReferenceID")


    # Materials (Updated: MaterialType -> Category, added SubType)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        MaterialID INTEGER PRIMARY KEY AUTOINCREMENT,
        MaterialName TEXT NOT NULL UNIQUE,
        Category TEXT, 
        SubType TEXT,  
        UnitOfMeasure TEXT,
        CostPerUnit REAL,
        QuantityInStock REAL,
        SupplierID INTEGER,
        LastStockUpdate TEXT,
        ReferenceID TEXT,
        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID) ON DELETE SET NULL
    )
    ''')
    _add_column_if_not_exists(cursor, "materials", "Category", "TEXT") # Was MaterialType
    _add_column_if_not_exists(cursor, "materials", "SubType", "TEXT")
    _add_column_if_not_exists(cursor, "materials", "SupplierID", "INTEGER")
    _add_column_if_not_exists(cursor, "materials", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "materials", "ReferenceID")


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
        ReferenceID TEXT,
        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID) ON DELETE SET NULL
    )
    ''')
    _add_column_if_not_exists(cursor, "products", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "products", "ReferenceID")


    # Projects
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
        ReferenceID TEXT,
        FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID) ON DELETE RESTRICT 
    )
    ''')
    _add_column_if_not_exists(cursor, "projects", "CustomerID", "INTEGER REFERENCES customers(CustomerID) ON DELETE RESTRICT")
    _add_column_if_not_exists(cursor, "projects", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "projects", "ReferenceID")


    # ProjectMaterials (NEW)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_materials (
        ProjectMaterialID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectID INTEGER NOT NULL,
        MaterialID INTEGER NOT NULL,
        QuantityUsed REAL NOT NULL,
        CostPerUnitAtTimeOfUse REAL,
        Notes TEXT,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE CASCADE,
        FOREIGN KEY (MaterialID) REFERENCES materials (MaterialID) ON DELETE CASCADE
    )
    ''')


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
        ReferenceID TEXT,
        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID) ON DELETE CASCADE,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE SET NULL
    )
    ''')
    _add_column_if_not_exists(cursor, "supplier_services", "IsExpenseLogged", "INTEGER DEFAULT 0")
    _add_column_if_not_exists(cursor, "supplier_services", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "supplier_services", "ReferenceID")


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
        ReferenceID TEXT,
        FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID) ON DELETE SET NULL, 
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE SET NULL
    )
    ''')
    _add_column_if_not_exists(cursor, "orders", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "orders", "ReferenceID")


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
        SupplierServiceID INTEGER,
        ReceiptReference TEXT,
        ReferenceID TEXT,
        FOREIGN KEY (ProjectID) REFERENCES projects (ProjectID) ON DELETE SET NULL,
        FOREIGN KEY (SupplierServiceID) REFERENCES supplier_services(ServiceID) ON DELETE SET NULL
    )
    ''')
    _add_column_if_not_exists(cursor, "expenses", "SupplierServiceID", "INTEGER REFERENCES supplier_services(ServiceID) ON DELETE SET NULL")
    _add_column_if_not_exists(cursor, "expenses", "ReferenceID", "TEXT")
    _ensure_unique_index(cursor, "expenses", "ReferenceID")

    conn.commit()
    conn.close()
    print("INFO: Database schema initialized/verified.")

# --- Customer CRUD ---
def add_customer(name, email, phone, reference_id_input, bill_addr, ship_addr, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        INSERT INTO customers (CustomerName, Email, Phone, BillingAddress, ShippingAddress, RegistrationDate, Notes, ReferenceID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, bill_addr, ship_addr or bill_addr, reg_date, notes, None)) # Insert with None ReferenceID first
        customer_id = cursor.lastrowid

        final_reference_id = reference_id_input if reference_id_input and reference_id_input.strip() else f"CUST-{customer_id:06d}"
        
        # Check if this generated/inputted ID already exists for another customer (excluding current one if it were an update)
        cursor.execute("SELECT CustomerID FROM customers WHERE ReferenceID = ? AND CustomerID != ?", (final_reference_id, customer_id))
        if cursor.fetchone():
            conn.rollback() # Important: rollback before raising
            raise ValueError(f"Reference ID '{final_reference_id}' already exists for another customer.")

        cursor.execute("UPDATE customers SET ReferenceID = ? WHERE CustomerID = ?", (final_reference_id, customer_id))
        conn.commit()
    except ValueError: # Re-raise ValueError from above check
        raise
    except sqlite3.IntegrityError as e: # Catch other potential integrity errors, though UNIQUE on ReferenceID is primary concern
        conn.rollback()
        raise ValueError(f"Could not add customer. Reference ID '{final_reference_id}' might be in use or another integrity issue occurred. DB Error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred while adding customer: {e}")
    finally:
        conn.close()

# ... (get_all_customers, get_customer_by_id, update_customer, delete_customer - remain largely the same as your latest version, ensure update_customer handles ReferenceID update carefully) ...
def get_all_customers(search_term=""): # From your version
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

def get_customer_by_id(customer_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE CustomerID = ?", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return customer

def update_customer(cust_id, name, email, phone, reference_id_input, bill_addr, ship_addr, notes): # From your version, minor adjustment for clarity
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        current_customer_row = get_customer_by_id(cust_id)
        if not current_customer_row:
            raise ValueError(f"Customer with ID {cust_id} not found.")
        
        final_reference_id = current_customer_row['ReferenceID'] # Default to current
        
        if reference_id_input and reference_id_input.strip():
            if reference_id_input.strip() != current_customer_row['ReferenceID']: # If it's a new, non-empty ID
                final_reference_id = reference_id_input.strip()
        elif not current_customer_row['ReferenceID']: # If current is NULL/empty and input is also NULL/empty
            final_reference_id = f"CUST-{cust_id:06d}" # Generate one if it was missing

        # Check for uniqueness if final_reference_id changed or was just generated
        if final_reference_id != current_customer_row['ReferenceID'] or not current_customer_row['ReferenceID']:
            cursor.execute("SELECT CustomerID FROM customers WHERE ReferenceID = ? AND CustomerID != ?", (final_reference_id, cust_id))
            if cursor.fetchone():
                conn.rollback()
                raise ValueError(f"Reference ID '{final_reference_id}' already exists for another customer.")

        cursor.execute('''
        UPDATE customers
        SET CustomerName = ?, Email = ?, Phone = ?, ReferenceID = ?, BillingAddress = ?, ShippingAddress = ?, Notes = ?
        WHERE CustomerID = ?
        ''', (name, email, phone, final_reference_id, bill_addr, ship_addr, notes, cust_id))
        conn.commit()
    except ValueError: # Re-raise
        raise
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Could not update customer. Reference ID '{final_reference_id}' might be in use or another integrity issue. DB Error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred while updating customer: {e}")
    finally:
        conn.close()

def delete_customer(customer_id): # From your version (with ON DELETE RESTRICT for invoices, it should prevent this)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check for explicit project links if ON DELETE SET NULL was used for projects.CustomerID
        cursor.execute("SELECT 1 FROM projects WHERE CustomerID = ?", (customer_id,))
        if cursor.fetchone():
            raise ValueError("Customer has existing projects. Cannot delete directly. Please reassign or delete projects first if your DB constraints allow.")

        # Invoices have ON DELETE RESTRICT, so this delete will fail if invoices exist
        cursor.execute("DELETE FROM customers WHERE CustomerID = ?", (customer_id,))
        if cursor.rowcount == 0:
            print(f"Warning: No customer found with ID {customer_id} to delete, or delete was restricted by FK.")
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Cannot delete customer (ID: {customer_id}). They have dependent records (e.g., Invoices, Projects with RESTRICT). Details: {e}")
    except ValueError: # From explicit check above
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

# --- Supplier CRUD --- (Using your latest versions)
def add_supplier(name, contact_person, email, phone, address): # From your version
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
    except sqlite3.IntegrityError: # Catches UNIQUE constraint on SupplierName or ReferenceID
        conn.rollback()
        raise ValueError(f"Supplier name '{name}' or generated ReferenceID '{reference_id}' already exists.")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_all_suppliers(search_term=""): # From your version
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

def get_supplier_by_id(supplier_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM suppliers WHERE SupplierID = ?", (supplier_id,))
    supplier = cursor.fetchone()
    conn.close()
    return supplier

def update_supplier(sup_id, name, contact_person, email, phone, address): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # ReferenceID is auto-generated and typically not updated by user for suppliers
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
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def delete_supplier(supplier_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM suppliers WHERE SupplierID = ?", (supplier_id,))
        conn.commit()
    except sqlite3.IntegrityError as e: # Will be caught if supplier is linked and FK is RESTRICT
        conn.rollback()
        raise ValueError(f"Cannot delete supplier (ID: {supplier_id}). They are referenced in Materials, Products, or Services. Error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()


# --- Material CRUD (Updated for Category/SubType) ---
def add_material(name, category, subtype, unit, cost_unit, qty, supplier_id): # Signature changed
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        INSERT INTO materials (MaterialName, Category, SubType, UnitOfMeasure, CostPerUnit, QuantityInStock, SupplierID, LastStockUpdate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, subtype, unit, cost_unit, qty, supplier_id, last_update))
        material_id = cursor.lastrowid
        reference_id = f"MAT-{material_id:06d}"
        cursor.execute("UPDATE materials SET ReferenceID = ? WHERE MaterialID = ?", (reference_id, material_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Material name '{name}' or generated ReferenceID '{reference_id}' already exists.")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_all_materials(search_term=""): # Updated to use Category and join Supplier
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT m.*, s.SupplierName
    FROM materials m
    LEFT JOIN suppliers s ON m.SupplierID = s.SupplierID
    """
    params = []
    if search_term:
        # Using Category instead of MaterialType for search
        query += " WHERE (m.MaterialName LIKE ? OR m.Category LIKE ? OR m.SubType LIKE ? OR s.SupplierName LIKE ? OR m.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term])
    query += " ORDER BY m.MaterialName"
    cursor.execute(query, params)
    materials = cursor.fetchall()
    conn.close()
    return materials

def get_material_by_id(material_id): # Updated to join Supplier
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT m.*, s.SupplierName 
    FROM materials m
    LEFT JOIN suppliers s ON m.SupplierID = s.SupplierID
    WHERE m.MaterialID = ?
    """, (material_id,))
    material = cursor.fetchone()
    conn.close()
    return material

def update_material(mat_id, name, category, subtype, unit, cost_unit, qty, supplier_id): # Signature changed
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        # ReferenceID is auto-generated and typically not updated by user for materials
        cursor.execute('''
        UPDATE materials
        SET MaterialName = ?, Category = ?, SubType = ?, UnitOfMeasure = ?, CostPerUnit = ?,
            QuantityInStock = ?, SupplierID = ?, LastStockUpdate = ?
        WHERE MaterialID = ?
        ''', (name, category, subtype, unit, cost_unit, qty, supplier_id, last_update, mat_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Material name '{name}' might already exist for another material.")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def delete_material(material_id): # From your version (ON DELETE CASCADE for ProjectMaterials)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM materials WHERE MaterialID = ?", (material_id,))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Cannot delete material (ID: {material_id}). It might be used in project_materials if ON DELETE CASCADE failed or is not set. Error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_distinct_material_categories(): # From previous combined response
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Category FROM materials WHERE Category IS NOT NULL AND Category != '' ORDER BY Category")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

def get_materials_by_category(category): # From previous combined response
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT m.*, s.SupplierName
        FROM materials m
        LEFT JOIN suppliers s ON m.SupplierID = s.SupplierID
        WHERE m.Category = ? 
        ORDER BY m.MaterialName
    """
    cursor.execute(query, (category,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_supplier_name_by_id(supplier_id): # From previous combined response
    if not supplier_id:
        return "N/A"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SupplierName FROM suppliers WHERE SupplierID = ?", (supplier_id,))
    row = cursor.fetchone()
    conn.close()
    return row['SupplierName'] if row else "N/A"


# --- Product CRUD (using your latest, ReferenceID added) ---
def add_product(name, sku, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path): # From your version
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
        except sqlite3.IntegrityError: # Should not happen if SKU is already unique and RefID is based on it or new PK
            conn.rollback()
            raise ValueError(f"Generated Reference ID '{reference_id}' for product already exists (highly unlikely).")
        conn.commit()
    except sqlite3.IntegrityError: # Primarily for SKU UNIQUE constraint
        conn.rollback()
        raise ValueError(f"Product SKU '{sku}' already exists.")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_all_products(search_term=""): # From your version
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

def get_product_by_id(product_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, s.SupplierName 
        FROM products p
        LEFT JOIN suppliers s ON p.SupplierID = s.SupplierID
        WHERE p.ProductID = ?
    """, (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def update_product(prod_id, name, sku, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        new_reference_id = sku if sku and sku.strip() else f"PROD-{prod_id:06d}"
        # Check uniqueness of new SKU and new_reference_id EXCLUDING current product
        if sku:
            cursor.execute("SELECT ProductID FROM products WHERE SKU = ? AND ProductID != ?", (sku, prod_id))
            if cursor.fetchone():
                conn.rollback()
                raise ValueError(f"New SKU '{sku}' already exists for another product.")
        if new_reference_id: # This check is more critical if ReferenceID can be manually set differently from SKU
            cursor.execute("SELECT ProductID FROM products WHERE ReferenceID = ? AND ProductID != ?", (new_reference_id, prod_id))
            if cursor.fetchone():
                conn.rollback()
                raise ValueError(f"New ReferenceID '{new_reference_id}' already exists for another product.")

        cursor.execute('''
        UPDATE products
        SET ProductName = ?, SKU = ?, ReferenceID = ?, Description = ?, Category = ?, MaterialType = ?, Dimensions = ?,
            CostPrice = ?, SellingPrice = ?, QuantityInStock = ?, ReorderLevel = ?, SupplierID = ?,
            ImagePath = ?, LastStockUpdate = ?
        WHERE ProductID = ?
        ''', (name, sku, new_reference_id, desc, category, material_type, dims, cost, sell, qty, reorder, supplier_id, image_path, last_update, prod_id))
        conn.commit()
    except ValueError: # Re-raise
        raise
    except sqlite3.IntegrityError: # Fallback, though specific checks are above
        conn.rollback()
        raise ValueError(f"Update failed for product. New SKU '{sku}' or Reference ID '{new_reference_id}' might already exist (fallback check).")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def update_product_stock(product_id, quantity_change): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE products SET QuantityInStock = QuantityInStock + ?, LastStockUpdate = ? WHERE ProductID = ?",
                       (quantity_change, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), product_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def delete_product(product_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        product_row = get_product_by_id(product_id) # Fetch product to get ImagePath
        if product_row:
            product = dict(product_row)
            image_path_to_delete = product.get('ImagePath')
            if image_path_to_delete and os.path.exists(image_path_to_delete):
                try:
                    os.remove(image_path_to_delete)
                    print(f"INFO: Deleted image file {image_path_to_delete}")
                except OSError as e_img:
                    print(f"WARNING: Error deleting image file {image_path_to_delete}: {e_img}")
        
        cursor.execute("DELETE FROM products WHERE ProductID = ?", (product_id,))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Cannot delete product (ID: {product_id}). It is referenced in order items. Error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()


# --- Project CRUD (using your latest versions, ReferenceID added) ---
def add_project(name, customer_id, start_date, end_date, status, budget, description): # From your version
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
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_all_projects(search_term=""): # From your version
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

def get_project_by_id(project_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.CustomerName, c.ReferenceID as CustomerRefID
        FROM projects p
        LEFT JOIN customers c ON p.CustomerID = c.CustomerID
        WHERE p.ProjectID = ?
    """, (project_id,))
    project = cursor.fetchone()
    conn.close()
    return project

def update_project(proj_id, name, customer_id, start_date, end_date, status, budget, description): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # ReferenceID is auto-generated and typically not updated by user for projects
        cursor.execute('''
        UPDATE projects
        SET ProjectName = ?, CustomerID = ?, StartDate = ?, EndDate = ?, Status = ?, Budget = ?, Description = ?
        WHERE ProjectID = ?
        ''', (name, customer_id, start_date, end_date, status, budget, description, proj_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def delete_project(project_id): # From your version (Invoices have ON DELETE RESTRICT)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Explicitly delete ProjectMaterials first due to ON DELETE CASCADE on ProjectMaterials.ProjectID
        cursor.execute("DELETE FROM project_materials WHERE ProjectID = ?", (project_id,))
        
        cursor.execute("DELETE FROM projects WHERE ProjectID = ?", (project_id,))
        if cursor.rowcount == 0:
             print(f"Warning: No project found with ID {project_id} to delete, or delete was restricted by FK (e.g. Invoices).")
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Cannot delete project (ID: {project_id}). It has dependent records (e.g., Invoices). Details: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()


# --- ProjectMaterials (NEW) ---
def add_material_to_project(project_id, material_id, quantity_used, cost_per_unit_at_time_of_use, notes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO project_materials (ProjectID, MaterialID, QuantityUsed, CostPerUnitAtTimeOfUse, Notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, material_id, quantity_used, cost_per_unit_at_time_of_use, notes))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise Exception(f"Database error when adding material to project: {e}")
    finally:
        conn.close()

def get_materials_for_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pm.ProjectMaterialID, pm.QuantityUsed, pm.CostPerUnitAtTimeOfUse, pm.Notes,
               m.MaterialID, m.MaterialName, m.UnitOfMeasure
        FROM project_materials pm
        JOIN materials m ON pm.MaterialID = m.MaterialID
        WHERE pm.ProjectID = ?
    ''', (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def remove_material_from_project(project_material_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        material_to_return = cursor.execute(
            "SELECT MaterialID, QuantityUsed FROM project_materials WHERE ProjectMaterialID = ?",
            (project_material_id,)
        ).fetchone()

        cursor.execute("DELETE FROM project_materials WHERE ProjectMaterialID = ?", (project_material_id,))
        conn.commit()

        if material_to_return:
            update_material_stock(material_to_return['MaterialID'], material_to_return['QuantityUsed']) # Positive to add back
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Database error when removing material from project: {e}")
    finally:
        conn.close()


# --- Supplier Service CRUD (using your latest, ReferenceID added) ---
def add_supplier_service(supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description): # From your version
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
            supplier_row = get_supplier_by_id(supplier_id) # Assumes this function exists and works
            supplier_name_for_expense = dict(supplier_row)['SupplierName'] if supplier_row else f"Supplier ID: {supplier_id}"
            
            expense_desc = f"Service: {service_name} (Ref: {reference_id}) by {supplier_name_for_expense}"
            if service_type: expense_desc += f" ({service_type})"

            # The add_expense function now has SupplierServiceID field
            # Pass service_pk_id to link the expense to this service
            new_expense_pk_id = add_expense(
                exp_date=service_date, desc=expense_desc, category="Supplier Services", amount=cost,
                vendor=supplier_name_for_expense, project_id=project_id,
                receipt_ref=f"ServRef: {reference_id}" + (f", ReceiptFile: {os.path.basename(receipt_path)}" if receipt_path and os.path.exists(receipt_path) else ""),
                supplier_service_id=service_pk_id, # NEWLY ADDED PARAMETER
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
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_all_supplier_services(search_term=""): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT ss.*, s.SupplierName, p.ProjectName, p.ReferenceID as ProjectRefID
    FROM supplier_services ss
    JOIN suppliers s ON ss.SupplierID = s.SupplierID
    LEFT JOIN projects p ON ss.ProjectID = p.ProjectID
    """
    params = []
    if search_term:
        query += " WHERE (ss.ServiceName LIKE ? OR ss.ServiceType LIKE ? OR s.SupplierName LIKE ? OR p.ProjectName LIKE ? OR ss.Description LIKE ? OR ss.ReferenceID LIKE ? OR p.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term, term, term])
    query += " ORDER BY ss.ServiceDate DESC, ss.ServiceID DESC"
    cursor.execute(query, params)
    services = cursor.fetchall()
    conn.close()
    return services

def get_supplier_service_by_id(service_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT ss.*, s.SupplierName, p.ProjectName, p.ReferenceID as ProjectRefID
    FROM supplier_services ss
    JOIN suppliers s ON ss.SupplierID = s.SupplierID
    LEFT JOIN projects p ON ss.ProjectID = p.ProjectID
    WHERE ss.ServiceID = ?
    """, (service_id,))
    service = cursor.fetchone()
    conn.close()
    return service

def update_supplier_service(service_id, supplier_id, project_id, service_name, service_type, service_date, cost, receipt_path, description, is_expense_logged_param): # From your version
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

        # This warning logic about expense review is good.
        if old_service_data and old_service_data.get('IsExpenseLogged'):
            cost_changed = old_service_data.get('Cost') != cost
            date_changed = old_service_data.get('ServiceDate') != service_date
            if cost_changed or date_changed:
                 print(f"WARNING in database.py update_supplier_service: Service ID {service_id} details changed. Associated auto-logged expense might need manual review.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()
        
def update_supplier_service_receipt_path(service_id, receipt_path): # Added earlier for app.py
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE supplier_services SET ReceiptPath = ? WHERE ServiceID = ?", (receipt_path, service_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"Error updating receipt path for service {service_id}: {e}")
    finally:
        conn.close()

def delete_supplier_service(service_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        service_info_row = get_supplier_service_by_id(service_id)
        if service_info_row:
            service_info = dict(service_info_row)
            if service_info.get('ReceiptPath') and os.path.exists(service_info['ReceiptPath']):
                try:
                    os.remove(service_info['ReceiptPath'])
                except OSError as e_img:
                    print(f"WARNING: Error deleting receipt file {service_info['ReceiptPath']}: {e_img}")

            if service_info.get('IsExpenseLogged'):
                # Find and delete the associated expense if it was auto-logged
                cursor.execute("DELETE FROM expenses WHERE SupplierServiceID = ?", (service_id,))
                if cursor.rowcount > 0:
                    print(f"INFO: Auto-deleted expense linked to SupplierServiceID {service_id}.")
                else:
                    print(f"INFO: Service ID {service_id} was marked as expense logged, but no direct expense link found via SupplierServiceID. Manual expense review might be needed.")


        cursor.execute("DELETE FROM supplier_services WHERE ServiceID = ?", (service_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_services_for_project(project_id): # For project edit page
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ss.*, s.SupplierName 
        FROM supplier_services ss
        LEFT JOIN suppliers s ON ss.SupplierID = s.SupplierID
        WHERE ss.ProjectID = ?
        ORDER BY ss.ServiceDate DESC
    ''', (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


# --- Order & Order Item CRUD (using your latest, ReferenceID added) ---
# ... (functions as in your latest database (3).py, ensuring ReferenceID generation and handling) ...
# --- Expense CRUD (updated to include SupplierServiceID and ReferenceID) ---
def add_expense(exp_date, desc, category, amount, vendor, project_id, receipt_ref, supplier_service_id=None, is_internal_call=False): # Added supplier_service_id
    conn = get_db_connection()
    cursor = conn.cursor()
    expense_pk_id = None
    try:
        cursor.execute('''
        INSERT INTO expenses (ExpenseDate, Description, Category, Amount, Vendor, ProjectID, ReceiptReference, SupplierServiceID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (exp_date, desc, category, amount, vendor, project_id, receipt_ref, supplier_service_id))
        expense_pk_id = cursor.lastrowid
        reference_id = f"EXP-{expense_pk_id:06d}"
        cursor.execute("UPDATE expenses SET ReferenceID = ? WHERE ExpenseID = ?", (reference_id, expense_pk_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        if not is_internal_call:
            raise Exception(f"An unexpected error occurred: {e}")
        else:
            print(f"INTERNAL ERROR during add_expense (desc: '{desc}', amount: {amount}): {e}")
            return None # Return None on failure for internal calls
    finally:
        conn.close()
    return expense_pk_id

def get_all_expenses(search_term=""): # Updated to join SupplierServices for service name
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT e.*, p.ProjectName, p.ReferenceID as ProjectRefID, serv.ServiceName as SupplierServiceName, serv.ReferenceID as ServiceRefID
    FROM expenses e
    LEFT JOIN projects p ON e.ProjectID = p.ProjectID
    LEFT JOIN supplier_services serv ON e.SupplierServiceID = serv.ServiceID
    """
    params = []
    if search_term:
        query += " WHERE (e.Description LIKE ? OR e.Category LIKE ? OR e.Vendor LIKE ? OR p.ProjectName LIKE ? OR p.ReferenceID LIKE ? OR e.ReferenceID LIKE ? OR serv.ServiceName LIKE ? OR serv.ReferenceID LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term, term, term, term])
    query += " ORDER BY e.ExpenseDate DESC, e.ExpenseID DESC"
    cursor.execute(query, params)
    expenses = cursor.fetchall()
    conn.close()
    return expenses


# --- Invoice CRUD (using your latest, ReferenceID generation improved) ---
# ... (functions as in your latest database (3).py) ...
# --- Functions for Customer Detail Page --- (from your latest)
# ... (get_orders_by_customer_id, get_invoices_by_customer_id, get_projects_by_customer_id) ...

# All other CRUD functions (Orders, OrderItems, Invoices) from your provided `database (3).py`
# should be placed here, ensuring they handle ReferenceID generation and updates similarly if needed.
# For brevity, I'm omitting the direct paste of those if they are largely unchanged from your file,
# but they are essential for `app.py` to function.

# --- Helper ---
def rows_to_dicts(rows): # From your version
    if not rows:
        return []
    # Check if it's a single sqlite3.Row object first
    if isinstance(rows, sqlite3.Row):
        return [dict(rows)] # Wrap single row in a list of dict
    
    # Then check if it's a list of sqlite3.Row objects
    if rows and isinstance(rows[0], sqlite3.Row):
        return [dict(row) for row in rows]
    
    # If it's already a list of dicts (less likely from db functions directly)
    if rows and isinstance(rows[0], dict):
        return rows
        
    return [] # Fallback for unexpected type or empty list


# Call init_db() once when the module is imported or explicitly.
# For Streamlit deployment, it's often better to call init_db()
# at the start of your app.py if you're using ephemeral storage or want to ensure schema.
if __name__ == "__main__":
    print(f"Database will be created/accessed at: {DATABASE_NAME}")
    init_db()
    print("Database setup/verification complete.")

# Ensure all other functions from your `database (3).py` are copied here.
# Specifically, the complete CRUDs for Orders, OrderItems, Invoices, Expenses, etc.
# I've integrated the key changes related to ProjectMaterials and ReferenceIDs throughout.

# Example of a remaining function to copy from your database (3).py if not already covered or modified above:
# (Ensure you copy ALL of them that app.py uses)
# def get_projects_by_customer_id(customer_id): ...
# def get_order_items_by_order_id(order_id): ...
# def update_order_total(order_id): ...
# def get_invoices_by_customer_id(customer_id): ...
# def get_invoices_by_project_id(project_id): ...
# ... and so on for every function your app.py calls.

# --- PASTE REMAINING FUNCTIONS FROM YOUR database (3).py HERE ---
# --- (Orders, OrderItems, Invoices, Expenses specific CRUDs if not fully covered above) ---
# --- (Ensure they are consistent with the ReferenceID and schema changes) ---

# For instance, Order related functions (ensure they are complete from your file):
def add_order(order_date, customer_id, project_id, status, total_amount, payment_status, ship_addr, notes, reference_id_input=None): # From your version
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
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def add_order_item(order_id, product_id, quantity, unit_price, discount): # From your version
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
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_all_orders(search_term="", limit=None): # From your version
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

def get_order_by_id(order_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT o.*, c.CustomerName, c.ReferenceID as CustomerRefID, pr.ProjectName, pr.ReferenceID as ProjectRefID
    FROM orders o
    LEFT JOIN customers c ON o.CustomerID = c.CustomerID
    LEFT JOIN projects pr ON o.ProjectID = pr.ProjectID
    WHERE o.OrderID = ?
    """, (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order

def update_order_basic_info(order_id, order_date, customer_id, project_id, status, payment_status, ship_addr, notes, reference_id_input): # From your version
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
        elif not current_order.get('ReferenceID') and reference_id_input and reference_id_input.strip(): # If current is None/empty but input is provided
            final_reference_id = reference_id_input.strip()
        elif not current_order.get('ReferenceID') and not (reference_id_input and reference_id_input.strip()): # If both current and input are None/empty
             final_reference_id = f"ORD-{order_id:06d}"
        
        # Check uniqueness if final_reference_id changed or was just generated
        if final_reference_id != current_order.get('ReferenceID') or not current_order.get('ReferenceID'):
            cursor.execute("SELECT OrderID FROM orders WHERE ReferenceID = ? AND OrderID != ?", (final_reference_id, order_id))
            if cursor.fetchone():
                conn.rollback()
                raise ValueError(f"Reference ID '{final_reference_id}' already exists for another order.")

        cursor.execute('''
        UPDATE orders
        SET OrderDate = ?, CustomerID = ?, ProjectID = ?, OrderStatus = ?, ReferenceID = ?,
            PaymentStatus = ?, ShippingAddress = ?, Notes = ?
        WHERE OrderID = ?
        ''', (order_date, customer_id, project_id, status, final_reference_id, payment_status, ship_addr, notes, order_id))
        conn.commit()
    except ValueError: # Re-raise
        raise
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Update order failed. Reference ID '{final_reference_id}' might be in use. DB Error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_orders_by_customer_id(customer_id): # From your version
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

def get_order_items_by_order_id(order_id): # From your version
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

def update_order_total(order_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SUM(LineTotal) FROM order_items WHERE OrderID = ?", (order_id,))
        total_amount_tuple = cursor.fetchone()
        total_amount = total_amount_tuple[0] if total_amount_tuple and total_amount_tuple[0] is not None else 0.0
        cursor.execute("UPDATE orders SET TotalAmount = ? WHERE OrderID = ?", (total_amount, order_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

# Invoice functions from your version
def get_next_invoice_reference_id(): # From your version
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
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE InvoiceReferenceID LIKE ?", (like_pattern,))
            count_row = cursor.fetchone()
            next_num = (count_row[0] if count_row else 0) + 1
    conn.close()
    return f"INV-{year_month}-{next_num:04d}"

def add_invoice(invoice_reference_id, project_id, customer_id, issue_date, due_date, payment_date, total_amount, status, notes): # From your version
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
        elif "FOREIGN KEY constraint failed" in str(e):
             raise ValueError(f"Invalid ProjectID or CustomerID provided for the invoice. Ensure they exist. Details: {e}")
        raise Exception(f"Database integrity error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_all_invoices(search_term=""): # From your version
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

def get_invoice_by_id(invoice_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.*, p.ProjectName, p.ReferenceID as ProjectRefID, c.CustomerName, c.ReferenceID as CustomerRefID
    FROM invoices i
    JOIN projects p ON i.ProjectID = p.ProjectID
    JOIN customers c ON i.CustomerID = c.CustomerID
    WHERE i.InvoiceID = ?
    """, (invoice_id,))
    invoice = cursor.fetchone()
    conn.close()
    return invoice

def update_invoice(invoice_id, invoice_reference_id, project_id, customer_id, issue_date, due_date, payment_date, total_amount, status, notes): # From your version
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
        elif "FOREIGN KEY constraint failed" in str(e):
             raise ValueError(f"Invalid ProjectID or CustomerID during invoice update. Ensure they exist. Details: {e}")
        raise Exception(f"Database integrity error: {e}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def get_invoices_by_customer_id(customer_id): # From your version
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

def get_invoices_by_project_id(project_id): # From your version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT i.*, c.CustomerName, c.ReferenceID as CustomerRefID
    FROM invoices i
    JOIN customers c ON i.CustomerID = c.CustomerID
    WHERE i.ProjectID = ?
    ORDER BY i.IssueDate DESC
    ''', (project_id,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_projects_by_customer_id(customer_id): # From your version
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

