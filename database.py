import sqlite3
import os
from datetime import datetime

DATABASE_DIR = "data"
DATABASE_NAME = os.path.join(DATABASE_DIR, "furniture_management.db")
IMAGE_DIR = "images"

if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Customer Table
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

    # Product Table
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
        SupplierID INTEGER, -- We'll keep this simple for now, not enforcing foreign key to a full supplier table yet
        LastStockUpdate TEXT,
        ImagePath TEXT
    )
    ''')

    # Orders Table (Sales Book)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
        OrderDate TEXT NOT NULL,
        CustomerID INTEGER,
        ProjectID INTEGER, -- Simplified, not fully linked
        OrderStatus TEXT,
        TotalAmount REAL,
        PaymentStatus TEXT,
        ShippingAddress TEXT,
        Notes TEXT,
        FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID)
    )
    ''')

    # Order Items Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        OrderItemID INTEGER PRIMARY KEY AUTOINCREMENT,
        OrderID INTEGER NOT NULL,
        ProductID INTEGER NOT NULL,
        QuantitySold INTEGER,
        UnitPriceAtSale REAL,
        Discount REAL,
        LineTotal REAL,
        FOREIGN KEY (OrderID) REFERENCES orders (OrderID),
        FOREIGN KEY (ProductID) REFERENCES products (ProductID)
    )
    ''')

    # Expense Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        ExpenseID INTEGER PRIMARY KEY AUTOINCREMENT,
        ExpenseDate TEXT NOT NULL,
        Description TEXT NOT NULL,
        Category TEXT,
        Amount REAL NOT NULL,
        Vendor TEXT,
        ProjectID INTEGER,
        ReceiptReference TEXT
    )
    ''')
    
    # Add other tables (Suppliers, Materials, Tax, CashFlow, Projects) here similarly
    # For brevity, I'm focusing on the core ones for CRUD demo.

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
    ''', (name, email, phone, bill_addr, ship_addr, reg_date, notes))
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
    # Consider related orders before deleting, or use ON DELETE SET NULL/CASCADE
    cursor.execute("DELETE FROM customers WHERE CustomerID = ?", (customer_id,))
    conn.commit()
    conn.close()

# --- Product CRUD ---
def add_product(name, sku, desc, category, material, dims, cost, sell, qty, reorder, supplier_id, image_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        INSERT INTO products (ProductName, SKU, Description, Category, MaterialType, Dimensions, CostPrice, SellingPrice, QuantityInStock, ReorderLevel, SupplierID, LastStockUpdate, ImagePath)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, sku, desc, category, material, dims, cost, sell, qty, reorder, supplier_id, last_update, image_path))
        conn.commit()
    except sqlite3.IntegrityError as e: # For SKU unique constraint
        conn.close()
        raise e # Re-raise the exception to be caught by the app
    conn.close()


def get_all_products(search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM products"
    params = []
    if search_term:
        query += " WHERE ProductName LIKE ? OR SKU LIKE ? OR Category LIKE ?"
        params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
    query += " ORDER BY ProductName"
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

def update_product(prod_id, name, sku, desc, category, material, dims, cost, sell, qty, reorder, supplier_id, image_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
        UPDATE products
        SET ProductName = ?, SKU = ?, Description = ?, Category = ?, MaterialType = ?, Dimensions = ?,
            CostPrice = ?, SellingPrice = ?, QuantityInStock = ?, ReorderLevel = ?, SupplierID = ?,
            LastStockUpdate = ?, ImagePath = ?
        WHERE ProductID = ?
        ''', (name, sku, desc, category, material, dims, cost, sell, qty, reorder, supplier_id, last_update, image_path, prod_id))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        raise e
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
    # Consider related order items before deleting
    product = get_product_by_id(product_id) # Get image path before deleting
    if product and product['ImagePath'] and os.path.exists(product['ImagePath']):
        try:
            os.remove(product['ImagePath'])
        except OSError as e:
            print(f"Error deleting image file {product['ImagePath']}: {e}")

    cursor.execute("DELETE FROM products WHERE ProductID = ?", (product_id,))
    conn.commit()
    conn.close()

# --- Order CRUD (Simplified for demonstration) ---
def add_order(order_date, customer_id, status, total_amount, payment_status, ship_addr, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO orders (OrderDate, CustomerID, OrderStatus, TotalAmount, PaymentStatus, ShippingAddress, Notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_date, customer_id, status, total_amount, payment_status, ship_addr, notes))
    order_id = cursor.lastrowid # Get the ID of the inserted order
    conn.commit()
    conn.close()
    return order_id

def add_order_item(order_id, product_id, quantity, unit_price, discount, line_total):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO order_items (OrderID, ProductID, QuantitySold, UnitPriceAtSale, Discount, LineTotal)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (order_id, product_id, quantity, unit_price, discount, line_total))
    conn.commit()
    conn.close()

def get_all_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Join with customers for better display
    cursor.execute('''
    SELECT o.*, c.CustomerName
    FROM orders o
    LEFT JOIN customers c ON o.CustomerID = c.CustomerID
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
    
# --- Expense CRUD ---
def add_expense(exp_date, desc, category, amount, vendor, project_id, receipt_ref):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO expenses (ExpenseDate, Description, Category, Amount, Vendor, ProjectID, ReceiptReference)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (exp_date, desc, category, amount, vendor, project_id, receipt_ref))
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id

def get_all_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY ExpenseDate DESC")
    expenses = cursor.fetchall()
    conn.close()
    return expenses

# --- Helper to convert SQLite Row objects to list of dicts for st.dataframe ---
def rows_to_dicts(rows):
    return [dict(row) for row in rows]

# Initialize the database and tables when this module is first imported
init_db()