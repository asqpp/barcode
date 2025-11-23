"""
Barcode generation and printing module
"""
import os
import random
import string
from io import BytesIO

try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import mm, inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

BARCODE_DIR = "barcodes"

def ensure_barcode_dir():
    if not os.path.exists(BARCODE_DIR):
        os.makedirs(BARCODE_DIR)

def generate_barcode_number(prefix=""):
    """Generate a unique barcode number"""
    random_part = ''.join(random.choices(string.digits, k=10))
    if prefix:
        return f"{prefix}{random_part}"
    return random_part

def generate_ean13():
    """Generate valid EAN-13 barcode"""
    digits = [random.randint(0, 9) for _ in range(12)]

    # Calculate check digit
    odd_sum = sum(digits[::2])
    even_sum = sum(digits[1::2])
    total = odd_sum + even_sum * 3
    check_digit = (10 - (total % 10)) % 10
    digits.append(check_digit)

    return ''.join(map(str, digits))

def create_barcode_image(barcode_number, barcode_type='code128', product_name=None):
    """
    Create barcode image
    Supported types: code128, code39, ean13, ean8, upca, isbn13
    """
    if not BARCODE_AVAILABLE:
        return None, "python-barcode library not installed"

    ensure_barcode_dir()

    try:
        barcode_class = barcode.get_barcode_class(barcode_type)

        options = {
            'module_width': 0.3,
            'module_height': 15.0,
            'font_size': 10,
            'text_distance': 5.0,
            'quiet_zone': 6.5,
        }

        bc = barcode_class(barcode_number, writer=ImageWriter())
        filename = os.path.join(BARCODE_DIR, f"{barcode_number}")
        filepath = bc.save(filename, options=options)

        # Add product name if provided
        if product_name and PIL_AVAILABLE:
            img = Image.open(filepath)
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font = ImageFont.load_default()

            # Add product name at top
            text_bbox = draw.textbbox((0, 0), product_name, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            x = (img.width - text_width) // 2
            draw.text((x, 5), product_name, fill='black', font=font)
            img.save(filepath)

        return filepath, None

    except Exception as e:
        return None, str(e)

def create_barcode_label(barcode_number, product_name, price=None, size=None):
    """Create a complete label with barcode, name, and price"""
    if not PIL_AVAILABLE:
        return None, "Pillow library not installed"

    ensure_barcode_dir()

    # Create barcode first
    filepath, error = create_barcode_image(barcode_number)
    if error:
        return None, error

    # Load barcode image
    bc_img = Image.open(filepath)

    # Create new label image
    label_width = max(bc_img.width, 300)
    label_height = bc_img.height + 60

    label = Image.new('RGB', (label_width, label_height), 'white')
    draw = ImageDraw.Draw(label)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw product name
    y_pos = 5
    text_bbox = draw.textbbox((0, 0), product_name[:30], font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    x = (label_width - text_width) // 2
    draw.text((x, y_pos), product_name[:30], fill='black', font=font_large)
    y_pos += 20

    # Draw size if provided
    if size:
        size_text = f"Size: {size}"
        text_bbox = draw.textbbox((0, 0), size_text, font=font_small)
        text_width = text_bbox[2] - text_bbox[0]
        x = (label_width - text_width) // 2
        draw.text((x, y_pos), size_text, fill='black', font=font_small)
        y_pos += 18

    # Paste barcode
    bc_x = (label_width - bc_img.width) // 2
    label.paste(bc_img, (bc_x, y_pos))
    y_pos += bc_img.height + 5

    # Draw price if provided
    if price:
        price_text = f"${price:.2f}"
        text_bbox = draw.textbbox((0, 0), price_text, font=font_large)
        text_width = text_bbox[2] - text_bbox[0]
        x = (label_width - text_width) // 2
        draw.text((x, y_pos), price_text, fill='black', font=font_large)

    # Save label
    label_path = os.path.join(BARCODE_DIR, f"label_{barcode_number}.png")
    label.save(label_path)

    return label_path, None

def create_barcode_pdf(labels_data, output_path="barcode_labels.pdf", labels_per_row=3, labels_per_col=10):
    """
    Create PDF with multiple barcode labels for printing
    labels_data = [{'barcode': '123', 'name': 'Product', 'price': 10.00, 'quantity': 2}, ...]
    """
    if not REPORTLAB_AVAILABLE:
        return None, "reportlab library not installed"

    ensure_barcode_dir()

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Label dimensions
    label_width = (width - 20*mm) / labels_per_row
    label_height = (height - 20*mm) / labels_per_col

    margin_x = 10*mm
    margin_y = 10*mm

    current_row = 0
    current_col = 0

    for item in labels_data:
        quantity = item.get('quantity', 1)

        for _ in range(quantity):
            if current_col >= labels_per_row:
                current_col = 0
                current_row += 1

            if current_row >= labels_per_col:
                c.showPage()
                current_row = 0
                current_col = 0

            x = margin_x + current_col * label_width
            y = height - margin_y - (current_row + 1) * label_height

            # Draw label border
            c.rect(x, y, label_width - 2*mm, label_height - 2*mm)

            # Draw product name
            c.setFont("Helvetica-Bold", 8)
            name = item['name'][:20]
            c.drawCentredString(x + label_width/2 - mm, y + label_height - 10*mm, name)

            # Generate and draw barcode
            filepath, error = create_barcode_image(item['barcode'])
            if filepath:
                try:
                    c.drawImage(filepath, x + 3*mm, y + 8*mm,
                               width=label_width - 8*mm, height=label_height - 25*mm,
                               preserveAspectRatio=True)
                except:
                    pass

            # Draw price
            if item.get('price'):
                c.setFont("Helvetica-Bold", 10)
                c.drawCentredString(x + label_width/2 - mm, y + 3*mm, f"${item['price']:.2f}")

            current_col += 1

    c.save()
    return output_path, None

def print_barcode(filepath, printer_name=None):
    """
    Send barcode image to printer
    Uses system default printer if printer_name not specified
    """
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

def get_available_printers():
    """Get list of available printers"""
    import subprocess
    import platform

    try:
        system = platform.system()

        if system == "Windows":
            result = subprocess.run(
                ["wmic", "printer", "get", "name"],
                capture_output=True, text=True
            )
            printers = [p.strip() for p in result.stdout.split('\n')[1:] if p.strip()]
        else:  # Linux/macOS
            result = subprocess.run(
                ["lpstat", "-p"],
                capture_output=True, text=True
            )
            printers = []
            for line in result.stdout.split('\n'):
                if line.startswith('printer'):
                    parts = line.split()
                    if len(parts) >= 2:
                        printers.append(parts[1])

        return printers

    except Exception as e:
        return []
