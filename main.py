"""
Barcode & ERP System for Fancy/Dress Shops
Main Tkinter GUI Application
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, date
import os

# Import modules
from database import (
    init_database, create_product, get_products, get_product_by_id,
    get_product_by_barcode, update_product, delete_product, update_stock,
    create_category, get_categories, delete_category,
    create_supplier, get_suppliers, get_supplier_by_id, update_supplier, delete_supplier,
    create_customer, get_customers, get_customer_by_id, update_customer, delete_customer,
    get_accounts, generate_invoice_no, get_low_stock_products, get_connection
)
from accounting import (
    create_journal_entry, record_sale, record_purchase,
    record_payment_received, record_payment_made,
    get_journal_entries, get_trial_balance, get_income_statement, get_balance_sheet
)
from barcode_manager import (
    generate_barcode_number, generate_ean13, create_barcode_image,
    create_barcode_label, create_barcode_pdf, print_barcode, get_available_printers
)

class ERPApplication(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Barcode & ERP System - Fancy Shop")
        self.geometry("1200x700")
        self.configure(bg='#f0f0f0')

        # Initialize database
        init_database()

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # Create main container
        self.create_menu()
        self.create_notebook()

        # Cart for POS
        self.cart = []
        self.current_customer = None

    def configure_styles(self):
        self.style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'), background='#f0f0f0')
        self.style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'), background='#f0f0f0')
        self.style.configure('TButton', font=('Helvetica', 10))
        self.style.configure('Primary.TButton', font=('Helvetica', 10, 'bold'))
        self.style.configure('Treeview', font=('Helvetica', 9), rowheight=25)
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Trial Balance", command=self.show_trial_balance)
        reports_menu.add_command(label="Income Statement", command=self.show_income_statement)
        reports_menu.add_command(label="Balance Sheet", command=self.show_balance_sheet)
        reports_menu.add_separator()
        reports_menu.add_command(label="Low Stock Report", command=self.show_low_stock)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.pos_tab = ttk.Frame(self.notebook)
        self.products_tab = ttk.Frame(self.notebook)
        self.barcode_tab = ttk.Frame(self.notebook)
        self.purchases_tab = ttk.Frame(self.notebook)
        self.customers_tab = ttk.Frame(self.notebook)
        self.suppliers_tab = ttk.Frame(self.notebook)
        self.accounting_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.pos_tab, text="Point of Sale")
        self.notebook.add(self.products_tab, text="Products")
        self.notebook.add(self.barcode_tab, text="Barcodes")
        self.notebook.add(self.purchases_tab, text="Purchases")
        self.notebook.add(self.customers_tab, text="Customers")
        self.notebook.add(self.suppliers_tab, text="Suppliers")
        self.notebook.add(self.accounting_tab, text="Accounting")

        # Initialize tabs
        self.setup_dashboard()
        self.setup_pos()
        self.setup_products()
        self.setup_barcode()
        self.setup_purchases()
        self.setup_customers()
        self.setup_suppliers()
        self.setup_accounting()

    # ==================== DASHBOARD ====================
    def setup_dashboard(self):
        frame = self.dashboard_tab

        ttk.Label(frame, text="Dashboard", style='Title.TLabel').pack(pady=10)

        # Stats frame
        stats_frame = ttk.Frame(frame)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        # Statistics cards
        self.create_stat_card(stats_frame, "Total Products", self.get_product_count(), 0)
        self.create_stat_card(stats_frame, "Low Stock Items", self.get_low_stock_count(), 1)
        self.create_stat_card(stats_frame, "Today's Sales", f"${self.get_today_sales():.2f}", 2)
        self.create_stat_card(stats_frame, "Total Customers", self.get_customer_count(), 3)

        # Recent activity
        ttk.Label(frame, text="Recent Sales", style='Header.TLabel').pack(pady=(20, 5), padx=20, anchor='w')

        columns = ('invoice', 'date', 'customer', 'amount', 'status')
        self.recent_sales_tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.recent_sales_tree.heading(col, text=col.title())
            self.recent_sales_tree.column(col, width=120)

        self.recent_sales_tree.pack(fill=tk.X, padx=20, pady=5)

        ttk.Button(frame, text="Refresh Dashboard", command=self.refresh_dashboard).pack(pady=10)

    def create_stat_card(self, parent, title, value, col):
        card = ttk.LabelFrame(parent, text=title)
        card.grid(row=0, column=col, padx=10, pady=5, sticky='nsew')
        parent.columnconfigure(col, weight=1)

        ttk.Label(card, text=str(value), font=('Helvetica', 24, 'bold')).pack(pady=10)

    def get_product_count(self):
        return len(get_products())

    def get_low_stock_count(self):
        return len(get_low_stock_products())

    def get_today_sales(self):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(total_amount) FROM sales WHERE date(sale_date) = date("now")')
            result = cursor.fetchone()[0]
            return result or 0

    def get_customer_count(self):
        return len(get_customers())

    def refresh_dashboard(self):
        # Refresh stats
        for widget in self.dashboard_tab.winfo_children():
            widget.destroy()
        self.setup_dashboard()

    # ==================== POINT OF SALE ====================
    def setup_pos(self):
        frame = self.pos_tab

        # Left panel - Product search and cart
        left_panel = ttk.Frame(frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Search
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Barcode/Search:").pack(side=tk.LEFT)
        self.pos_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.pos_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<Return>', self.pos_search)

        ttk.Button(search_frame, text="Add", command=self.pos_search).pack(side=tk.LEFT)

        # Cart
        ttk.Label(left_panel, text="Shopping Cart", style='Header.TLabel').pack(pady=5)

        columns = ('product', 'qty', 'price', 'total')
        self.cart_tree = ttk.Treeview(left_panel, columns=columns, show='headings', height=12)

        for col in columns:
            self.cart_tree.heading(col, text=col.title())
        self.cart_tree.column('product', width=200)
        self.cart_tree.column('qty', width=50)
        self.cart_tree.column('price', width=80)
        self.cart_tree.column('total', width=80)

        self.cart_tree.pack(fill=tk.BOTH, expand=True)

        # Cart buttons
        cart_btn_frame = ttk.Frame(left_panel)
        cart_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(cart_btn_frame, text="Remove Item", command=self.remove_cart_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(cart_btn_frame, text="Clear Cart", command=self.clear_cart).pack(side=tk.LEFT, padx=2)

        # Right panel - Totals and checkout
        right_panel = ttk.LabelFrame(frame, text="Checkout")
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Customer selection
        ttk.Label(right_panel, text="Customer:").pack(pady=5)
        self.pos_customer_var = tk.StringVar()
        self.pos_customer_combo = ttk.Combobox(right_panel, textvariable=self.pos_customer_var, width=25)
        self.pos_customer_combo.pack(pady=5)
        self.refresh_pos_customers()

        # Totals
        ttk.Separator(right_panel, orient='horizontal').pack(fill=tk.X, pady=10)

        self.subtotal_var = tk.StringVar(value="$0.00")
        self.discount_var = tk.StringVar(value="0")
        self.tax_var = tk.StringVar(value="0")
        self.total_var = tk.StringVar(value="$0.00")

        ttk.Label(right_panel, text="Subtotal:").pack()
        ttk.Label(right_panel, textvariable=self.subtotal_var, font=('Helvetica', 12)).pack()

        ttk.Label(right_panel, text="Discount %:").pack(pady=(10, 0))
        ttk.Entry(right_panel, textvariable=self.discount_var, width=10).pack()

        ttk.Label(right_panel, text="Tax %:").pack(pady=(5, 0))
        ttk.Entry(right_panel, textvariable=self.tax_var, width=10).pack()

        ttk.Button(right_panel, text="Calculate", command=self.calculate_total).pack(pady=10)

        ttk.Label(right_panel, text="Total:").pack()
        ttk.Label(right_panel, textvariable=self.total_var, font=('Helvetica', 18, 'bold')).pack()

        # Payment
        ttk.Separator(right_panel, orient='horizontal').pack(fill=tk.X, pady=10)

        ttk.Label(right_panel, text="Payment Amount:").pack()
        self.payment_var = tk.StringVar()
        ttk.Entry(right_panel, textvariable=self.payment_var, width=15).pack(pady=5)

        ttk.Button(right_panel, text="Complete Sale", style='Primary.TButton',
                   command=self.complete_sale).pack(pady=10)

    def refresh_pos_customers(self):
        customers = get_customers()
        customer_list = ['Walk-in Customer'] + [f"{c['id']} - {c['name']}" for c in customers]
        self.pos_customer_combo['values'] = customer_list
        self.pos_customer_combo.set('Walk-in Customer')

    def pos_search(self, event=None):
        search = self.pos_search_var.get().strip()
        if not search:
            return

        # Try barcode first
        product = get_product_by_barcode(search)

        if not product:
            # Search by name
            products = get_products(search)
            if products:
                product = products[0]

        if product:
            self.add_to_cart(product)
            self.pos_search_var.set('')
        else:
            messagebox.showwarning("Not Found", f"Product '{search}' not found")

    def add_to_cart(self, product):
        # Check if already in cart
        for i, item in enumerate(self.cart):
            if item['id'] == product['id']:
                self.cart[i]['qty'] += 1
                self.cart[i]['total'] = self.cart[i]['qty'] * self.cart[i]['price']
                self.refresh_cart()
                return

        # Add new item
        self.cart.append({
            'id': product['id'],
            'name': product['name'],
            'qty': 1,
            'price': product['selling_price'],
            'total': product['selling_price'],
            'cost': product['purchase_price']
        })
        self.refresh_cart()

    def refresh_cart(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        subtotal = 0
        for item in self.cart:
            self.cart_tree.insert('', 'end', values=(
                item['name'], item['qty'], f"${item['price']:.2f}", f"${item['total']:.2f}"
            ))
            subtotal += item['total']
        self.subtotal_var.set(f"${subtotal:.2f}")
        self.calculate_total()

    def remove_cart_item(self):
        selected = self.cart_tree.selection()
        if selected:
            index = self.cart_tree.index(selected[0])
            del self.cart[index]
            self.refresh_cart()

    def clear_cart(self):
        self.cart = []
        self.refresh_cart()

    def calculate_total(self):
        subtotal = sum(item['total'] for item in self.cart)
        try:
            discount_pct = float(self.discount_var.get() or 0)
            tax_pct = float(self.tax_var.get() or 0)
        except ValueError:
            discount_pct = tax_pct = 0

        discount = subtotal * (discount_pct / 100)
        after_discount = subtotal - discount
        tax = after_discount * (tax_pct / 100)
        total = after_discount + tax

        self.total_var.set(f"${total:.2f}")
        return total

    def complete_sale(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to cart")
            return

        total = self.calculate_total()
        try:
            paid = float(self.payment_var.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Invalid payment amount")
            return

        if paid < total:
            if not messagebox.askyesno("Partial Payment",
                f"Payment ${paid:.2f} is less than total ${total:.2f}. Continue?"):
                return

        # Get customer ID
        customer_id = None
        customer_str = self.pos_customer_var.get()
        if customer_str and customer_str != 'Walk-in Customer':
            customer_id = int(customer_str.split(' - ')[0])

        # Create sale
        with get_connection() as conn:
            cursor = conn.cursor()

            invoice_no = generate_invoice_no('INV')
            subtotal = sum(item['total'] for item in self.cart)
            discount_pct = float(self.discount_var.get() or 0)
            tax_pct = float(self.tax_var.get() or 0)
            discount = subtotal * (discount_pct / 100)
            tax = (subtotal - discount) * (tax_pct / 100)

            cursor.execute('''
                INSERT INTO sales (invoice_no, customer_id, sale_date, subtotal, discount, tax,
                                   total_amount, paid_amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (invoice_no, customer_id, date.today(), subtotal, discount, tax, total, paid,
                  'paid' if paid >= total else 'partial'))

            sale_id = cursor.lastrowid

            # Add sale items and update stock
            total_cost = 0
            for item in self.cart:
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['id'], item['qty'], item['price'], item['total']))

                # Update stock
                update_stock(item['id'], -item['qty'], 'sale', 'sale', sale_id)
                total_cost += item['cost'] * item['qty']

            conn.commit()

            # Record accounting entry
            record_sale(sale_id, total, total_cost, paid)

        messagebox.showinfo("Success", f"Sale completed!\nInvoice: {invoice_no}\nChange: ${max(0, paid - total):.2f}")

        # Clear cart
        self.clear_cart()
        self.payment_var.set('')
        self.discount_var.set('0')
        self.tax_var.set('0')

    # ==================== PRODUCTS ====================
    def setup_products(self):
        frame = self.products_tab

        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Button(toolbar, text="Add Product", command=self.add_product_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit", command=self.edit_product).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete", command=self.delete_product_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_products).pack(side=tk.LEFT, padx=2)

        # Search
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.product_search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.product_search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind('<Return>', lambda e: self.refresh_products())
        ttk.Button(toolbar, text="Go", command=self.refresh_products).pack(side=tk.LEFT, padx=2)

        # Category management
        ttk.Button(toolbar, text="Categories", command=self.manage_categories).pack(side=tk.RIGHT, padx=2)

        # Products list
        columns = ('id', 'barcode', 'name', 'category', 'price', 'stock', 'size', 'color')
        self.products_tree = ttk.Treeview(frame, columns=columns, show='headings')

        for col in columns:
            self.products_tree.heading(col, text=col.title())
        self.products_tree.column('id', width=50)
        self.products_tree.column('barcode', width=120)
        self.products_tree.column('name', width=200)
        self.products_tree.column('category', width=100)
        self.products_tree.column('price', width=80)
        self.products_tree.column('stock', width=60)
        self.products_tree.column('size', width=60)
        self.products_tree.column('color', width=80)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)

        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_products()

    def refresh_products(self):
        self.products_tree.delete(*self.products_tree.get_children())
        search = self.product_search_var.get() if hasattr(self, 'product_search_var') else None
        products = get_products(search)

        for p in products:
            self.products_tree.insert('', 'end', values=(
                p['id'], p['barcode'], p['name'], p['category_name'] or '',
                f"${p['selling_price']:.2f}", p['quantity'], p['size'] or '', p['color'] or ''
            ))

    def add_product_dialog(self):
        dialog = ProductDialog(self, "Add Product")
        self.wait_window(dialog)
        self.refresh_products()

    def edit_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a product")
            return

        product_id = self.products_tree.item(selected[0])['values'][0]
        product = get_product_by_id(product_id)
        dialog = ProductDialog(self, "Edit Product", product)
        self.wait_window(dialog)
        self.refresh_products()

    def delete_product_action(self):
        selected = self.products_tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm", "Delete selected product?"):
            product_id = self.products_tree.item(selected[0])['values'][0]
            delete_product(product_id)
            self.refresh_products()

    def manage_categories(self):
        dialog = CategoryDialog(self)
        self.wait_window(dialog)

    # ==================== BARCODES ====================
    def setup_barcode(self):
        frame = self.barcode_tab

        ttk.Label(frame, text="Barcode Generator", style='Title.TLabel').pack(pady=10)

        # Options frame
        options = ttk.LabelFrame(frame, text="Generate Barcode")
        options.pack(fill=tk.X, padx=20, pady=10)

        # Barcode type
        row1 = ttk.Frame(options)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="Type:").pack(side=tk.LEFT, padx=5)
        self.barcode_type_var = tk.StringVar(value='code128')
        barcode_types = ['code128', 'code39', 'ean13', 'ean8', 'upca']
        ttk.Combobox(row1, textvariable=self.barcode_type_var, values=barcode_types, width=15).pack(side=tk.LEFT)

        # Product selection
        row2 = ttk.Frame(options)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Product:").pack(side=tk.LEFT, padx=5)
        self.barcode_product_var = tk.StringVar()
        self.barcode_product_combo = ttk.Combobox(row2, textvariable=self.barcode_product_var, width=40)
        self.barcode_product_combo.pack(side=tk.LEFT, padx=5)
        self.refresh_barcode_products()

        # Manual barcode entry
        row3 = ttk.Frame(options)
        row3.pack(fill=tk.X, pady=5)
        ttk.Label(row3, text="Or Enter Barcode:").pack(side=tk.LEFT, padx=5)
        self.manual_barcode_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.manual_barcode_var, width=20).pack(side=tk.LEFT)
        ttk.Button(row3, text="Generate Number", command=self.generate_barcode_number_action).pack(side=tk.LEFT, padx=5)

        # Quantity
        row4 = ttk.Frame(options)
        row4.pack(fill=tk.X, pady=5)
        ttk.Label(row4, text="Quantity:").pack(side=tk.LEFT, padx=5)
        self.barcode_qty_var = tk.StringVar(value="1")
        ttk.Entry(row4, textvariable=self.barcode_qty_var, width=10).pack(side=tk.LEFT)

        # Buttons
        btn_frame = ttk.Frame(options)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Generate Barcode", command=self.generate_barcode_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Create Label", command=self.create_label_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Print", command=self.print_barcode_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Create PDF", command=self.create_pdf_action).pack(side=tk.LEFT, padx=5)

        # Preview
        preview_frame = ttk.LabelFrame(frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.barcode_preview_label = ttk.Label(preview_frame, text="Barcode preview will appear here")
        self.barcode_preview_label.pack(pady=20)

        # Batch generation
        batch_frame = ttk.LabelFrame(frame, text="Batch Print Labels")
        batch_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(batch_frame, text="Select multiple products and generate PDF labels for printing").pack(pady=5)
        ttk.Button(batch_frame, text="Select Products for Batch Print", command=self.batch_print_dialog).pack(pady=5)

    def refresh_barcode_products(self):
        products = get_products()
        product_list = [f"{p['id']} - {p['name']} ({p['barcode'] or 'No barcode'})" for p in products]
        self.barcode_product_combo['values'] = product_list

    def generate_barcode_number_action(self):
        barcode_type = self.barcode_type_var.get()
        if barcode_type == 'ean13':
            number = generate_ean13()
        else:
            number = generate_barcode_number()
        self.manual_barcode_var.set(number)

    def generate_barcode_action(self):
        barcode_num = self.manual_barcode_var.get().strip()

        if not barcode_num:
            # Get from selected product
            product_str = self.barcode_product_var.get()
            if product_str:
                product_id = int(product_str.split(' - ')[0])
                product = get_product_by_id(product_id)
                if product and product['barcode']:
                    barcode_num = product['barcode']

        if not barcode_num:
            messagebox.showwarning("Error", "Please enter barcode number or select product")
            return

        filepath, error = create_barcode_image(barcode_num, self.barcode_type_var.get())

        if error:
            messagebox.showerror("Error", error)
        else:
            self.show_barcode_preview(filepath)
            messagebox.showinfo("Success", f"Barcode saved to {filepath}")

    def create_label_action(self):
        barcode_num = self.manual_barcode_var.get().strip()
        product_name = "Product"
        price = None

        product_str = self.barcode_product_var.get()
        if product_str:
            product_id = int(product_str.split(' - ')[0])
            product = get_product_by_id(product_id)
            if product:
                barcode_num = barcode_num or product['barcode']
                product_name = product['name']
                price = product['selling_price']

        if not barcode_num:
            messagebox.showwarning("Error", "Please enter barcode number")
            return

        filepath, error = create_barcode_label(barcode_num, product_name, price)

        if error:
            messagebox.showerror("Error", error)
        else:
            self.show_barcode_preview(filepath)
            messagebox.showinfo("Success", f"Label saved to {filepath}")

    def show_barcode_preview(self, filepath):
        try:
            from PIL import Image, ImageTk
            img = Image.open(filepath)
            img.thumbnail((400, 300))
            photo = ImageTk.PhotoImage(img)
            self.barcode_preview_label.configure(image=photo)
            self.barcode_preview_label.image = photo
            self.current_barcode_file = filepath
        except ImportError:
            self.barcode_preview_label.configure(text=f"Barcode saved: {filepath}")
            self.current_barcode_file = filepath

    def print_barcode_action(self):
        if hasattr(self, 'current_barcode_file') and self.current_barcode_file:
            printers = get_available_printers()
            if printers:
                printer = printers[0]  # Use default
                success, error = print_barcode(self.current_barcode_file, printer)
                if success:
                    messagebox.showinfo("Success", "Sent to printer")
                else:
                    messagebox.showerror("Error", error)
            else:
                messagebox.showwarning("No Printer", "No printers found")
        else:
            messagebox.showwarning("Error", "Generate a barcode first")

    def create_pdf_action(self):
        product_str = self.barcode_product_var.get()
        if not product_str:
            messagebox.showwarning("Error", "Please select a product")
            return

        product_id = int(product_str.split(' - ')[0])
        product = get_product_by_id(product_id)

        try:
            qty = int(self.barcode_qty_var.get())
        except ValueError:
            qty = 1

        labels_data = [{
            'barcode': product['barcode'],
            'name': product['name'],
            'price': product['selling_price'],
            'quantity': qty
        }]

        filepath, error = create_barcode_pdf(labels_data)
        if error:
            messagebox.showerror("Error", error)
        else:
            messagebox.showinfo("Success", f"PDF saved to {filepath}")

    def batch_print_dialog(self):
        dialog = BatchPrintDialog(self)
        self.wait_window(dialog)

    # ==================== PURCHASES ====================
    def setup_purchases(self):
        frame = self.purchases_tab

        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Button(toolbar, text="New Purchase", command=self.new_purchase_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="View Details", command=self.view_purchase).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Make Payment", command=self.purchase_payment).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_purchases).pack(side=tk.LEFT, padx=2)

        # Purchases list
        columns = ('id', 'invoice', 'supplier', 'date', 'total', 'paid', 'status')
        self.purchases_tree = ttk.Treeview(frame, columns=columns, show='headings')

        for col in columns:
            self.purchases_tree.heading(col, text=col.title())
            self.purchases_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.purchases_tree.yview)
        self.purchases_tree.configure(yscrollcommand=scrollbar.set)

        self.purchases_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_purchases()

    def refresh_purchases(self):
        self.purchases_tree.delete(*self.purchases_tree.get_children())
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, s.name as supplier_name FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.purchase_date DESC
            ''')
            for row in cursor.fetchall():
                self.purchases_tree.insert('', 'end', values=(
                    row['id'], row['invoice_no'], row['supplier_name'] or '',
                    row['purchase_date'], f"${row['total_amount']:.2f}",
                    f"${row['paid_amount']:.2f}", row['status']
                ))

    def new_purchase_dialog(self):
        dialog = PurchaseDialog(self)
        self.wait_window(dialog)
        self.refresh_purchases()

    def view_purchase(self):
        selected = self.purchases_tree.selection()
        if not selected:
            return
        purchase_id = self.purchases_tree.item(selected[0])['values'][0]
        # Show purchase details
        messagebox.showinfo("Purchase", f"Purchase ID: {purchase_id}")

    def purchase_payment(self):
        selected = self.purchases_tree.selection()
        if not selected:
            return

        purchase_id = self.purchases_tree.item(selected[0])['values'][0]
        amount = simpledialog.askfloat("Payment", "Enter payment amount:")

        if amount and amount > 0:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT supplier_id FROM purchases WHERE id = ?', (purchase_id,))
                supplier_id = cursor.fetchone()[0]

                cursor.execute('UPDATE purchases SET paid_amount = paid_amount + ? WHERE id = ?',
                             (amount, purchase_id))
                cursor.execute('UPDATE purchases SET status = "paid" WHERE id = ? AND paid_amount >= total_amount',
                             (purchase_id,))
                conn.commit()

                record_payment_made(supplier_id, amount, f'PUR-{purchase_id}')

            messagebox.showinfo("Success", "Payment recorded")
            self.refresh_purchases()

    # ==================== CUSTOMERS ====================
    def setup_customers(self):
        frame = self.customers_tab

        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Button(toolbar, text="Add Customer", command=self.add_customer_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit", command=self.edit_customer).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete", command=self.delete_customer_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_customers).pack(side=tk.LEFT, padx=2)

        # Customers list
        columns = ('id', 'name', 'phone', 'email', 'balance')
        self.customers_tree = ttk.Treeview(frame, columns=columns, show='headings')

        for col in columns:
            self.customers_tree.heading(col, text=col.title())
            self.customers_tree.column(col, width=150)

        self.customers_tree.pack(fill=tk.BOTH, expand=True)
        self.refresh_customers()

    def refresh_customers(self):
        self.customers_tree.delete(*self.customers_tree.get_children())
        for c in get_customers():
            self.customers_tree.insert('', 'end', values=(
                c['id'], c['name'], c['phone'] or '', c['email'] or '', f"${c['balance']:.2f}"
            ))

    def add_customer_dialog(self):
        dialog = CustomerDialog(self, "Add Customer")
        self.wait_window(dialog)
        self.refresh_customers()
        self.refresh_pos_customers()

    def edit_customer(self):
        selected = self.customers_tree.selection()
        if not selected:
            return
        customer_id = self.customers_tree.item(selected[0])['values'][0]
        customer = get_customer_by_id(customer_id)
        dialog = CustomerDialog(self, "Edit Customer", customer)
        self.wait_window(dialog)
        self.refresh_customers()

    def delete_customer_action(self):
        selected = self.customers_tree.selection()
        if selected and messagebox.askyesno("Confirm", "Delete customer?"):
            customer_id = self.customers_tree.item(selected[0])['values'][0]
            delete_customer(customer_id)
            self.refresh_customers()

    # ==================== SUPPLIERS ====================
    def setup_suppliers(self):
        frame = self.suppliers_tab

        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Button(toolbar, text="Add Supplier", command=self.add_supplier_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit", command=self.edit_supplier).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete", command=self.delete_supplier_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_suppliers).pack(side=tk.LEFT, padx=2)

        # Suppliers list
        columns = ('id', 'name', 'contact', 'phone', 'email', 'balance')
        self.suppliers_tree = ttk.Treeview(frame, columns=columns, show='headings')

        for col in columns:
            self.suppliers_tree.heading(col, text=col.title())
            self.suppliers_tree.column(col, width=120)

        self.suppliers_tree.pack(fill=tk.BOTH, expand=True)
        self.refresh_suppliers()

    def refresh_suppliers(self):
        self.suppliers_tree.delete(*self.suppliers_tree.get_children())
        for s in get_suppliers():
            self.suppliers_tree.insert('', 'end', values=(
                s['id'], s['name'], s['contact_person'] or '', s['phone'] or '',
                s['email'] or '', f"${s['balance']:.2f}"
            ))

    def add_supplier_dialog(self):
        dialog = SupplierDialog(self, "Add Supplier")
        self.wait_window(dialog)
        self.refresh_suppliers()

    def edit_supplier(self):
        selected = self.suppliers_tree.selection()
        if not selected:
            return
        supplier_id = self.suppliers_tree.item(selected[0])['values'][0]
        supplier = get_supplier_by_id(supplier_id)
        dialog = SupplierDialog(self, "Edit Supplier", supplier)
        self.wait_window(dialog)
        self.refresh_suppliers()

    def delete_supplier_action(self):
        selected = self.suppliers_tree.selection()
        if selected and messagebox.askyesno("Confirm", "Delete supplier?"):
            supplier_id = self.suppliers_tree.item(selected[0])['values'][0]
            delete_supplier(supplier_id)
            self.refresh_suppliers()

    # ==================== ACCOUNTING ====================
    def setup_accounting(self):
        frame = self.accounting_tab

        ttk.Label(frame, text="Accounting & Journal Entries", style='Title.TLabel').pack(pady=10)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="New Journal Entry", command=self.new_journal_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Chart of Accounts", command=self.show_chart_of_accounts).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_journal_entries).pack(side=tk.LEFT, padx=2)

        # Journal entries list
        columns = ('id', 'date', 'reference', 'description')
        self.journal_tree = ttk.Treeview(frame, columns=columns, show='headings')

        for col in columns:
            self.journal_tree.heading(col, text=col.title())
        self.journal_tree.column('id', width=50)
        self.journal_tree.column('date', width=100)
        self.journal_tree.column('reference', width=120)
        self.journal_tree.column('description', width=400)

        self.journal_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.refresh_journal_entries()

    def refresh_journal_entries(self):
        self.journal_tree.delete(*self.journal_tree.get_children())
        entries = get_journal_entries()
        for e in entries:
            self.journal_tree.insert('', 'end', values=(
                e['id'], e['entry_date'], e['reference'] or '', e['description']
            ))

    def new_journal_entry(self):
        dialog = JournalEntryDialog(self)
        self.wait_window(dialog)
        self.refresh_journal_entries()

    def show_chart_of_accounts(self):
        dialog = tk.Toplevel(self)
        dialog.title("Chart of Accounts")
        dialog.geometry("500x400")

        columns = ('code', 'name', 'type', 'balance')
        tree = ttk.Treeview(dialog, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col.title())

        for acc in get_accounts():
            tree.insert('', 'end', values=(
                acc['code'], acc['name'], acc['account_type'], f"${acc['balance']:.2f}"
            ))

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ==================== REPORTS ====================
    def show_trial_balance(self):
        dialog = tk.Toplevel(self)
        dialog.title("Trial Balance")
        dialog.geometry("500x400")

        columns = ('code', 'name', 'debit', 'credit')
        tree = ttk.Treeview(dialog, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col.title())

        total_debit = total_credit = 0
        for acc in get_trial_balance():
            if acc['account_type'] in ('asset', 'expense'):
                debit = acc['balance'] if acc['balance'] > 0 else 0
                credit = -acc['balance'] if acc['balance'] < 0 else 0
            else:
                debit = -acc['balance'] if acc['balance'] < 0 else 0
                credit = acc['balance'] if acc['balance'] > 0 else 0

            total_debit += debit
            total_credit += credit
            tree.insert('', 'end', values=(
                acc['code'], acc['name'], f"${debit:.2f}", f"${credit:.2f}"
            ))

        tree.insert('', 'end', values=('', 'TOTAL', f"${total_debit:.2f}", f"${total_credit:.2f}"))
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def show_income_statement(self):
        data = get_income_statement()
        msg = f"Revenue: ${data['revenue']:.2f}\n"
        msg += f"Expenses: ${data['expenses']:.2f}\n"
        msg += f"Net Income: ${data['net_income']:.2f}"
        messagebox.showinfo("Income Statement", msg)

    def show_balance_sheet(self):
        data = get_balance_sheet()
        msg = f"Assets: ${data['assets']:.2f}\n"
        msg += f"Liabilities: ${data['liabilities']:.2f}\n"
        msg += f"Equity: ${data['equity']:.2f}\n"
        msg += f"Total Liab & Equity: ${data['total_liab_equity']:.2f}"
        messagebox.showinfo("Balance Sheet", msg)

    def show_low_stock(self):
        products = get_low_stock_products()
        if not products:
            messagebox.showinfo("Low Stock", "No low stock items")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Low Stock Report")
        dialog.geometry("600x400")

        columns = ('name', 'barcode', 'current', 'minimum')
        tree = ttk.Treeview(dialog, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col.title())

        for p in products:
            tree.insert('', 'end', values=(
                p['name'], p['barcode'], p['quantity'], p['min_stock']
            ))

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def backup_database(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db")]
        )
        if filepath:
            import shutil
            shutil.copy("erp_database.db", filepath)
            messagebox.showinfo("Success", f"Database backed up to {filepath}")

    def show_about(self):
        messagebox.showinfo("About", "Barcode & ERP System v1.0\nFor Fancy/Dress Shops\n\nFeatures:\n- Barcode Generation\n- Point of Sale\n- Inventory Management\n- Double-Entry Accounting\n- Purchase & Sales")


# ==================== DIALOGS ====================

class ProductDialog(tk.Toplevel):
    def __init__(self, parent, title, product=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x500")
        self.product = product

        # Form fields
        fields_frame = ttk.Frame(self)
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        self.entries = {}

        labels = ['Barcode', 'Name', 'Description', 'Category', 'Purchase Price',
                  'Selling Price', 'Quantity', 'Min Stock', 'Unit', 'Size', 'Color']
        keys = ['barcode', 'name', 'description', 'category_id', 'purchase_price',
                'selling_price', 'quantity', 'min_stock', 'unit', 'size', 'color']

        for label, key in zip(labels, keys):
            ttk.Label(fields_frame, text=label + ":").grid(row=row, column=0, sticky='w', pady=2)

            if key == 'category_id':
                var = tk.StringVar()
                combo = ttk.Combobox(fields_frame, textvariable=var, width=28)
                categories = get_categories()
                combo['values'] = [f"{c['id']} - {c['name']}" for c in categories]
                combo.grid(row=row, column=1, pady=2)
                self.entries[key] = var

                if product and product['category_id']:
                    for c in categories:
                        if c['id'] == product['category_id']:
                            var.set(f"{c['id']} - {c['name']}")
                            break
            elif key == 'barcode':
                frame = ttk.Frame(fields_frame)
                frame.grid(row=row, column=1, pady=2)
                var = tk.StringVar(value=product[key] if product and product[key] else '')
                entry = ttk.Entry(frame, textvariable=var, width=20)
                entry.pack(side=tk.LEFT)
                ttk.Button(frame, text="Gen", command=lambda v=var: v.set(generate_barcode_number())).pack(side=tk.LEFT)
                self.entries[key] = var
            else:
                var = tk.StringVar(value=str(product[key]) if product and product[key] else '')
                ttk.Entry(fields_frame, textvariable=var, width=30).grid(row=row, column=1, pady=2)
                self.entries[key] = var

            row += 1

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

    def save(self):
        data = {}
        for key, var in self.entries.items():
            val = var.get()
            if key == 'category_id':
                data[key] = int(val.split(' - ')[0]) if val else None
            elif key in ('purchase_price', 'selling_price'):
                data[key] = float(val) if val else 0
            elif key in ('quantity', 'min_stock'):
                data[key] = int(val) if val else 0
            else:
                data[key] = val

        if not data.get('name'):
            messagebox.showerror("Error", "Name is required")
            return

        if self.product:
            update_product(self.product['id'], data)
        else:
            create_product(data)

        self.destroy()


class CustomerDialog(tk.Toplevel):
    def __init__(self, parent, title, customer=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x250")
        self.customer = customer

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.entries = {}
        for i, (label, key) in enumerate([('Name', 'name'), ('Phone', 'phone'),
                                           ('Email', 'email'), ('Address', 'address')]):
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky='w', pady=5)
            var = tk.StringVar(value=customer[key] if customer and customer[key] else '')
            ttk.Entry(frame, textvariable=var, width=30).grid(row=i, column=1, pady=5)
            self.entries[key] = var

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

    def save(self):
        data = {k: v.get() for k, v in self.entries.items()}
        if not data.get('name'):
            messagebox.showerror("Error", "Name required")
            return

        if self.customer:
            update_customer(self.customer['id'], data)
        else:
            create_customer(data)
        self.destroy()


class SupplierDialog(tk.Toplevel):
    def __init__(self, parent, title, supplier=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x300")
        self.supplier = supplier

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.entries = {}
        for i, (label, key) in enumerate([('Name', 'name'), ('Contact Person', 'contact_person'),
                                           ('Phone', 'phone'), ('Email', 'email'), ('Address', 'address')]):
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky='w', pady=5)
            var = tk.StringVar(value=supplier[key] if supplier and supplier[key] else '')
            ttk.Entry(frame, textvariable=var, width=30).grid(row=i, column=1, pady=5)
            self.entries[key] = var

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

    def save(self):
        data = {k: v.get() for k, v in self.entries.items()}
        if not data.get('name'):
            messagebox.showerror("Error", "Name required")
            return

        if self.supplier:
            update_supplier(self.supplier['id'], data)
        else:
            create_supplier(data)
        self.destroy()


class CategoryDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Manage Categories")
        self.geometry("400x300")

        # Add new
        add_frame = ttk.Frame(self)
        add_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(add_frame, text="Name:").pack(side=tk.LEFT)
        self.cat_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.cat_name_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(add_frame, text="Add", command=self.add_category).pack(side=tk.LEFT)

        # List
        self.cat_listbox = tk.Listbox(self)
        self.cat_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Button(self, text="Delete Selected", command=self.delete_category).pack(pady=5)

        self.refresh_categories()

    def refresh_categories(self):
        self.cat_listbox.delete(0, tk.END)
        for c in get_categories():
            self.cat_listbox.insert(tk.END, f"{c['id']} - {c['name']}")

    def add_category(self):
        name = self.cat_name_var.get().strip()
        if name:
            create_category(name)
            self.cat_name_var.set('')
            self.refresh_categories()

    def delete_category(self):
        sel = self.cat_listbox.curselection()
        if sel:
            item = self.cat_listbox.get(sel[0])
            cat_id = int(item.split(' - ')[0])
            delete_category(cat_id)
            self.refresh_categories()


class PurchaseDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("New Purchase")
        self.geometry("600x500")

        self.items = []

        # Supplier selection
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="Supplier:").pack(side=tk.LEFT)
        self.supplier_var = tk.StringVar()
        self.supplier_combo = ttk.Combobox(top_frame, textvariable=self.supplier_var, width=30)
        suppliers = get_suppliers()
        self.supplier_combo['values'] = [f"{s['id']} - {s['name']}" for s in suppliers]
        self.supplier_combo.pack(side=tk.LEFT, padx=5)

        # Add item
        add_frame = ttk.LabelFrame(self, text="Add Item")
        add_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(add_frame, text="Product:").grid(row=0, column=0)
        self.product_var = tk.StringVar()
        product_combo = ttk.Combobox(add_frame, textvariable=self.product_var, width=30)
        products = get_products()
        product_combo['values'] = [f"{p['id']} - {p['name']}" for p in products]
        product_combo.grid(row=0, column=1)

        ttk.Label(add_frame, text="Qty:").grid(row=0, column=2)
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(add_frame, textvariable=self.qty_var, width=8).grid(row=0, column=3)

        ttk.Label(add_frame, text="Price:").grid(row=0, column=4)
        self.price_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.price_var, width=10).grid(row=0, column=5)

        ttk.Button(add_frame, text="Add", command=self.add_item).grid(row=0, column=6, padx=5)

        # Items list
        columns = ('product', 'qty', 'price', 'total')
        self.items_tree = ttk.Treeview(self, columns=columns, show='headings', height=8)
        for col in columns:
            self.items_tree.heading(col, text=col.title())
        self.items_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Total
        self.total_var = tk.StringVar(value="Total: $0.00")
        ttk.Label(self, textvariable=self.total_var, font=('Helvetica', 12, 'bold')).pack()

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save Purchase", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

    def add_item(self):
        product_str = self.product_var.get()
        if not product_str:
            return

        product_id = int(product_str.split(' - ')[0])
        product = get_product_by_id(product_id)

        try:
            qty = int(self.qty_var.get())
            price = float(self.price_var.get() or product['purchase_price'])
        except ValueError:
            return

        total = qty * price
        self.items.append({
            'product_id': product_id,
            'name': product['name'],
            'qty': qty,
            'price': price,
            'total': total
        })

        self.items_tree.insert('', 'end', values=(product['name'], qty, f"${price:.2f}", f"${total:.2f}"))
        grand_total = sum(i['total'] for i in self.items)
        self.total_var.set(f"Total: ${grand_total:.2f}")

    def save(self):
        if not self.items:
            messagebox.showwarning("Error", "Add items first")
            return

        supplier_str = self.supplier_var.get()
        supplier_id = int(supplier_str.split(' - ')[0]) if supplier_str else None

        total = sum(i['total'] for i in self.items)

        with get_connection() as conn:
            cursor = conn.cursor()

            invoice_no = generate_invoice_no('PUR')
            cursor.execute('''
                INSERT INTO purchases (invoice_no, supplier_id, purchase_date, total_amount, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (invoice_no, supplier_id, date.today(), total))

            purchase_id = cursor.lastrowid

            for item in self.items:
                cursor.execute('''
                    INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_price, total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (purchase_id, item['product_id'], item['qty'], item['price'], item['total']))

                update_stock(item['product_id'], item['qty'], 'purchase', 'purchase', purchase_id)

            conn.commit()
            record_purchase(purchase_id, total)

        messagebox.showinfo("Success", f"Purchase {invoice_no} created")
        self.destroy()


class JournalEntryDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("New Journal Entry")
        self.geometry("600x400")

        self.lines = []

        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header, text="Description:").pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(header, textvariable=self.desc_var, width=40).pack(side=tk.LEFT, padx=5)

        # Add line
        add_frame = ttk.LabelFrame(self, text="Add Line")
        add_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(add_frame, text="Account:").grid(row=0, column=0)
        self.account_var = tk.StringVar()
        acc_combo = ttk.Combobox(add_frame, textvariable=self.account_var, width=25)
        accounts = get_accounts()
        acc_combo['values'] = [f"{a['id']} - {a['code']} {a['name']}" for a in accounts]
        acc_combo.grid(row=0, column=1)

        ttk.Label(add_frame, text="Debit:").grid(row=0, column=2)
        self.debit_var = tk.StringVar(value="0")
        ttk.Entry(add_frame, textvariable=self.debit_var, width=10).grid(row=0, column=3)

        ttk.Label(add_frame, text="Credit:").grid(row=0, column=4)
        self.credit_var = tk.StringVar(value="0")
        ttk.Entry(add_frame, textvariable=self.credit_var, width=10).grid(row=0, column=5)

        ttk.Button(add_frame, text="Add", command=self.add_line).grid(row=0, column=6, padx=5)

        # Lines list
        columns = ('account', 'debit', 'credit')
        self.lines_tree = ttk.Treeview(self, columns=columns, show='headings', height=6)
        for col in columns:
            self.lines_tree.heading(col, text=col.title())
        self.lines_tree.pack(fill=tk.BOTH, expand=True, padx=10)

        # Totals
        self.totals_var = tk.StringVar(value="Debit: $0.00 | Credit: $0.00")
        ttk.Label(self, textvariable=self.totals_var).pack()

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save Entry", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

    def add_line(self):
        acc_str = self.account_var.get()
        if not acc_str:
            return

        account_id = int(acc_str.split(' - ')[0])
        account_name = acc_str.split(' - ')[1]

        try:
            debit = float(self.debit_var.get() or 0)
            credit = float(self.credit_var.get() or 0)
        except ValueError:
            return

        self.lines.append({'account_id': account_id, 'debit': debit, 'credit': credit})
        self.lines_tree.insert('', 'end', values=(account_name, f"${debit:.2f}", f"${credit:.2f}"))

        total_debit = sum(l['debit'] for l in self.lines)
        total_credit = sum(l['credit'] for l in self.lines)
        self.totals_var.set(f"Debit: ${total_debit:.2f} | Credit: ${total_credit:.2f}")

    def save(self):
        if not self.lines:
            messagebox.showwarning("Error", "Add lines first")
            return

        try:
            create_journal_entry(date.today(), self.desc_var.get(), self.lines)
            messagebox.showinfo("Success", "Journal entry created")
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))


class BatchPrintDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Batch Print Labels")
        self.geometry("500x400")

        ttk.Label(self, text="Select products and quantities for label printing").pack(pady=5)

        # Products list with checkboxes
        self.selected = {}
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for p in get_products():
            if p['barcode']:
                row = ttk.Frame(scrollable)
                row.pack(fill=tk.X, pady=2)

                var = tk.BooleanVar()
                ttk.Checkbutton(row, variable=var).pack(side=tk.LEFT)
                ttk.Label(row, text=p['name'][:30]).pack(side=tk.LEFT)

                qty_var = tk.StringVar(value="1")
                ttk.Entry(row, textvariable=qty_var, width=5).pack(side=tk.RIGHT)
                ttk.Label(row, text="Qty:").pack(side=tk.RIGHT)

                self.selected[p['id']] = {'check': var, 'qty': qty_var, 'product': p}

        ttk.Button(self, text="Generate PDF", command=self.generate).pack(pady=10)

    def generate(self):
        labels = []
        for pid, data in self.selected.items():
            if data['check'].get():
                p = data['product']
                try:
                    qty = int(data['qty'].get())
                except ValueError:
                    qty = 1
                labels.append({
                    'barcode': p['barcode'],
                    'name': p['name'],
                    'price': p['selling_price'],
                    'quantity': qty
                })

        if labels:
            filepath, error = create_barcode_pdf(labels)
            if error:
                messagebox.showerror("Error", error)
            else:
                messagebox.showinfo("Success", f"PDF saved to {filepath}")
                self.destroy()
        else:
            messagebox.showwarning("Error", "Select at least one product")


if __name__ == "__main__":
    app = ERPApplication()
    app.mainloop()
