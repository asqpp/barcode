"""
Database models and connection for ERP system
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE_NAME = "erp_database.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize all database tables"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Products/Inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                category_id INTEGER,
                purchase_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                quantity INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 5,
                unit TEXT DEFAULT 'pcs',
                size TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')

        # Suppliers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Chart of Accounts for double-entry
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                parent_id INTEGER,
                balance REAL DEFAULT 0,
                is_system INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES accounts(id)
            )
        ''')

        # Journal Entries (double-entry)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date DATE NOT NULL,
                reference TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Journal Entry Lines
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                FOREIGN KEY (entry_id) REFERENCES journal_entries(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        ''')

        # Purchases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE,
                supplier_id INTEGER,
                purchase_date DATE NOT NULL,
                total_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # Purchase Items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # Sales table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE,
                customer_id INTEGER,
                sale_date DATE NOT NULL,
                subtotal REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')

        # Sale Items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount REAL DEFAULT 0,
                total REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_type TEXT NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                payment_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Stock movements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        conn.commit()

        # Initialize default accounts
        _init_default_accounts(cursor)
        conn.commit()

def _init_default_accounts(cursor):
    """Initialize default chart of accounts"""
    default_accounts = [
        ('1000', 'Assets', 'asset', None, 1),
        ('1100', 'Cash', 'asset', 1, 1),
        ('1200', 'Bank', 'asset', 1, 1),
        ('1300', 'Accounts Receivable', 'asset', 1, 1),
        ('1400', 'Inventory', 'asset', 1, 1),
        ('2000', 'Liabilities', 'liability', None, 1),
        ('2100', 'Accounts Payable', 'liability', 6, 1),
        ('3000', 'Equity', 'equity', None, 1),
        ('3100', 'Capital', 'equity', 8, 1),
        ('3200', 'Retained Earnings', 'equity', 8, 1),
        ('4000', 'Revenue', 'revenue', None, 1),
        ('4100', 'Sales Revenue', 'revenue', 11, 1),
        ('5000', 'Expenses', 'expense', None, 1),
        ('5100', 'Cost of Goods Sold', 'expense', 13, 1),
        ('5200', 'Operating Expenses', 'expense', 13, 1),
    ]

    for code, name, acc_type, parent, is_system in default_accounts:
        cursor.execute('''
            INSERT OR IGNORE INTO accounts (code, name, account_type, parent_id, is_system)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, name, acc_type, parent, is_system))

# CRUD Operations for Products
def create_product(data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (barcode, name, description, category_id, purchase_price,
                                  selling_price, quantity, min_stock, unit, size, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['barcode'], data['name'], data.get('description'), data.get('category_id'),
              data.get('purchase_price', 0), data.get('selling_price', 0), data.get('quantity', 0),
              data.get('min_stock', 5), data.get('unit', 'pcs'), data.get('size'), data.get('color')))
        conn.commit()
        return cursor.lastrowid

def get_products(search=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if search:
            cursor.execute('''
                SELECT p.*, c.name as category_name FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.name LIKE ? OR p.barcode LIKE ? OR p.description LIKE ?
                ORDER BY p.name
            ''', (f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            cursor.execute('''
                SELECT p.*, c.name as category_name FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name
            ''')
        return cursor.fetchall()

def get_product_by_id(product_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        return cursor.fetchone()

def get_product_by_barcode(barcode):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE barcode = ?', (barcode,))
        return cursor.fetchone()

def update_product(product_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products SET barcode=?, name=?, description=?, category_id=?,
                               purchase_price=?, selling_price=?, quantity=?, min_stock=?,
                               unit=?, size=?, color=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (data['barcode'], data['name'], data.get('description'), data.get('category_id'),
              data.get('purchase_price', 0), data.get('selling_price', 0), data.get('quantity', 0),
              data.get('min_stock', 5), data.get('unit', 'pcs'), data.get('size'), data.get('color'),
              product_id))
        conn.commit()

def delete_product(product_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()

def update_stock(product_id, quantity_change, movement_type, reference_type=None, reference_id=None, notes=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET quantity = quantity + ? WHERE id = ?', (quantity_change, product_id))
        cursor.execute('''
            INSERT INTO stock_movements (product_id, movement_type, quantity, reference_type, reference_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product_id, movement_type, quantity_change, reference_type, reference_id, notes))
        conn.commit()

# CRUD Operations for Categories
def create_category(name, description=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        return cursor.lastrowid

def get_categories():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY name')
        return cursor.fetchall()

def delete_category(category_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()

# CRUD Operations for Suppliers
def create_supplier(data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO suppliers (name, contact_person, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data.get('contact_person'), data.get('phone'),
              data.get('email'), data.get('address')))
        conn.commit()
        return cursor.lastrowid

def get_suppliers():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM suppliers ORDER BY name')
        return cursor.fetchall()

def get_supplier_by_id(supplier_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,))
        return cursor.fetchone()

def update_supplier(supplier_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE suppliers SET name=?, contact_person=?, phone=?, email=?, address=?
            WHERE id=?
        ''', (data['name'], data.get('contact_person'), data.get('phone'),
              data.get('email'), data.get('address'), supplier_id))
        conn.commit()

def delete_supplier(supplier_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
        conn.commit()

# CRUD Operations for Customers
def create_customer(data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (name, phone, email, address)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data.get('phone'), data.get('email'), data.get('address')))
        conn.commit()
        return cursor.lastrowid

def get_customers():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY name')
        return cursor.fetchall()

def get_customer_by_id(customer_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        return cursor.fetchone()

def update_customer(customer_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers SET name=?, phone=?, email=?, address=?
            WHERE id=?
        ''', (data['name'], data.get('phone'), data.get('email'), data.get('address'), customer_id))
        conn.commit()

def delete_customer(customer_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        conn.commit()

# Accounts operations
def get_accounts():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts ORDER BY code')
        return cursor.fetchall()

def get_account_by_code(code):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE code = ?', (code,))
        return cursor.fetchone()

def get_account_by_id(account_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        return cursor.fetchone()

# Generate unique invoice numbers
def generate_invoice_no(prefix):
    with get_connection() as conn:
        cursor = conn.cursor()
        date_str = datetime.now().strftime('%Y%m%d')
        pattern = f'{prefix}{date_str}%'

        if prefix == 'PUR':
            cursor.execute('SELECT invoice_no FROM purchases WHERE invoice_no LIKE ? ORDER BY id DESC LIMIT 1', (pattern,))
        else:
            cursor.execute('SELECT invoice_no FROM sales WHERE invoice_no LIKE ? ORDER BY id DESC LIMIT 1', (pattern,))

        result = cursor.fetchone()
        if result:
            last_num = int(result[0][-4:])
            new_num = str(last_num + 1).zfill(4)
        else:
            new_num = '0001'

        return f'{prefix}{date_str}{new_num}'

def get_low_stock_products():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE quantity <= min_stock ORDER BY quantity')
        return cursor.fetchall()
