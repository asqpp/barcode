"""
Receipt generation and printing module
"""
import os
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import mm, inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

RECEIPT_DIR = "receipts"

def ensure_receipt_dir():
    if not os.path.exists(RECEIPT_DIR):
        os.makedirs(RECEIPT_DIR)

def generate_receipt_text(sale_data, items, shop_info=None):
    """Generate receipt as formatted text"""
    if shop_info is None:
        shop_info = {
            'name': 'FANCY DRESS SHOP',
            'address': '123 Fashion Street',
            'phone': '(555) 123-4567',
            'email': 'info@fancydress.com'
        }

    width = 40
    lines = []

    # Header
    lines.append('=' * width)
    lines.append(shop_info['name'].center(width))
    lines.append(shop_info['address'].center(width))
    lines.append(shop_info['phone'].center(width))
    lines.append('=' * width)
    lines.append('')

    # Invoice info
    lines.append(f"Invoice: {sale_data['invoice_no']}")
    lines.append(f"Date: {sale_data['date']}")
    lines.append(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    if sale_data.get('customer'):
        lines.append(f"Customer: {sale_data['customer']}")
    lines.append('-' * width)

    # Items
    lines.append(f"{'Item':<20} {'Qty':>4} {'Price':>7} {'Total':>7}")
    lines.append('-' * width)

    for item in items:
        name = item['name'][:18]
        qty = str(item['qty'])
        price = f"${item['price']:.2f}"
        total = f"${item['total']:.2f}"
        lines.append(f"{name:<20} {qty:>4} {price:>7} {total:>7}")

    lines.append('-' * width)

    # Totals
    lines.append(f"{'Subtotal:':<28} ${sale_data['subtotal']:>9.2f}")

    if sale_data.get('discount', 0) > 0:
        lines.append(f"{'Discount:':<28} -${sale_data['discount']:>8.2f}")

    if sale_data.get('tax', 0) > 0:
        lines.append(f"{'Tax:':<28} ${sale_data['tax']:>9.2f}")

    lines.append('=' * width)
    lines.append(f"{'TOTAL:':<28} ${sale_data['total']:>9.2f}")
    lines.append('=' * width)

    # Payment info
    lines.append(f"{'Paid:':<28} ${sale_data['paid']:>9.2f}")
    change = max(0, sale_data['paid'] - sale_data['total'])
    lines.append(f"{'Change:':<28} ${change:>9.2f}")

    if sale_data['paid'] < sale_data['total']:
        balance = sale_data['total'] - sale_data['paid']
        lines.append(f"{'Balance Due:':<28} ${balance:>9.2f}")

    lines.append('')
    lines.append('-' * width)
    lines.append('Thank you for shopping!'.center(width))
    lines.append('Please come again'.center(width))
    lines.append('-' * width)

    return '\n'.join(lines)

def save_receipt_text(receipt_text, invoice_no):
    """Save receipt as text file"""
    ensure_receipt_dir()
    filepath = os.path.join(RECEIPT_DIR, f"receipt_{invoice_no}.txt")
    with open(filepath, 'w') as f:
        f.write(receipt_text)
    return filepath

def generate_receipt_pdf(sale_data, items, shop_info=None, output_path=None):
    """Generate receipt as PDF"""
    if not REPORTLAB_AVAILABLE:
        return None, "reportlab library not installed"

    if shop_info is None:
        shop_info = {
            'name': 'FANCY DRESS SHOP',
            'address': '123 Fashion Street',
            'phone': '(555) 123-4567',
            'email': 'info@fancydress.com'
        }

    ensure_receipt_dir()

    if output_path is None:
        output_path = os.path.join(RECEIPT_DIR, f"receipt_{sale_data['invoice_no']}.pdf")

    # Receipt size (80mm thermal printer width)
    page_width = 80 * mm
    page_height = 200 * mm

    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    y = page_height - 10 * mm
    left_margin = 5 * mm
    right_margin = page_width - 5 * mm

    # Header
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(page_width / 2, y, shop_info['name'])
    y -= 12

    c.setFont("Helvetica", 8)
    c.drawCentredString(page_width / 2, y, shop_info['address'])
    y -= 10
    c.drawCentredString(page_width / 2, y, shop_info['phone'])
    y -= 12

    # Line
    c.line(left_margin, y, right_margin, y)
    y -= 12

    # Invoice info
    c.setFont("Helvetica", 8)
    c.drawString(left_margin, y, f"Invoice: {sale_data['invoice_no']}")
    y -= 10
    c.drawString(left_margin, y, f"Date: {sale_data['date']} {datetime.now().strftime('%H:%M')}")
    y -= 10

    if sale_data.get('customer'):
        c.drawString(left_margin, y, f"Customer: {sale_data['customer']}")
        y -= 10

    y -= 5
    c.line(left_margin, y, right_margin, y)
    y -= 12

    # Items header
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_margin, y, "Item")
    c.drawString(left_margin + 35 * mm, y, "Qty")
    c.drawString(left_margin + 45 * mm, y, "Price")
    c.drawRightString(right_margin, y, "Total")
    y -= 10

    c.line(left_margin, y, right_margin, y)
    y -= 10

    # Items
    c.setFont("Helvetica", 7)
    for item in items:
        name = item['name'][:20]
        c.drawString(left_margin, y, name)
        c.drawString(left_margin + 35 * mm, y, str(item['qty']))
        c.drawString(left_margin + 45 * mm, y, f"${item['price']:.2f}")
        c.drawRightString(right_margin, y, f"${item['total']:.2f}")
        y -= 10

    y -= 2
    c.line(left_margin, y, right_margin, y)
    y -= 12

    # Totals
    c.setFont("Helvetica", 8)
    c.drawString(left_margin, y, "Subtotal:")
    c.drawRightString(right_margin, y, f"${sale_data['subtotal']:.2f}")
    y -= 10

    if sale_data.get('discount', 0) > 0:
        c.drawString(left_margin, y, "Discount:")
        c.drawRightString(right_margin, y, f"-${sale_data['discount']:.2f}")
        y -= 10

    if sale_data.get('tax', 0) > 0:
        c.drawString(left_margin, y, "Tax:")
        c.drawRightString(right_margin, y, f"${sale_data['tax']:.2f}")
        y -= 10

    y -= 2
    c.setLineWidth(2)
    c.line(left_margin, y, right_margin, y)
    y -= 12

    # Total
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, y, "TOTAL:")
    c.drawRightString(right_margin, y, f"${sale_data['total']:.2f}")
    y -= 12

    c.setLineWidth(2)
    c.line(left_margin, y, right_margin, y)
    y -= 12

    # Payment
    c.setFont("Helvetica", 8)
    c.drawString(left_margin, y, "Paid:")
    c.drawRightString(right_margin, y, f"${sale_data['paid']:.2f}")
    y -= 10

    change = max(0, sale_data['paid'] - sale_data['total'])
    c.drawString(left_margin, y, "Change:")
    c.drawRightString(right_margin, y, f"${change:.2f}")
    y -= 10

    if sale_data['paid'] < sale_data['total']:
        balance = sale_data['total'] - sale_data['paid']
        c.setFont("Helvetica-Bold", 8)
        c.drawString(left_margin, y, "Balance Due:")
        c.drawRightString(right_margin, y, f"${balance:.2f}")
        y -= 10

    # Footer
    y -= 10
    c.setLineWidth(0.5)
    c.line(left_margin, y, right_margin, y)
    y -= 12

    c.setFont("Helvetica", 7)
    c.drawCentredString(page_width / 2, y, "Thank you for shopping!")
    y -= 10
    c.drawCentredString(page_width / 2, y, "Please come again")

    c.save()
    return output_path, None

def print_receipt(filepath, printer_name=None):
    """Send receipt to printer"""
    import subprocess
    import platform

    if not os.path.exists(filepath):
        return False, "File not found"

    try:
        system = platform.system()

        if system == "Windows":
            os.startfile(filepath, "print")
        elif system == "Darwin":  # macOS
            if printer_name:
                subprocess.run(["lpr", "-P", printer_name, filepath], check=True)
            else:
                subprocess.run(["lpr", filepath], check=True)
        else:  # Linux
            if printer_name:
                subprocess.run(["lpr", "-P", printer_name, filepath], check=True)
            else:
                subprocess.run(["lpr", filepath], check=True)

        return True, None

    except Exception as e:
        return False, str(e)

def print_receipt_to_thermal(receipt_text, printer_name=None):
    """Print text receipt to thermal printer using ESC/POS commands"""
    import subprocess
    import platform

    # ESC/POS commands
    ESC = b'\x1b'
    GS = b'\x1d'

    # Initialize printer
    init_printer = ESC + b'@'

    # Cut paper
    cut_paper = GS + b'V' + b'\x00'

    # Prepare data
    data = init_printer
    data += receipt_text.encode('utf-8')
    data += b'\n\n\n'
    data += cut_paper

    try:
        system = platform.system()

        if system == "Linux":
            if printer_name:
                process = subprocess.Popen(['lpr', '-P', printer_name, '-o', 'raw'],
                                          stdin=subprocess.PIPE)
            else:
                process = subprocess.Popen(['lpr', '-o', 'raw'],
                                          stdin=subprocess.PIPE)
            process.communicate(data)
            return True, None
        else:
            return False, "Thermal printing only supported on Linux"

    except Exception as e:
        return False, str(e)
