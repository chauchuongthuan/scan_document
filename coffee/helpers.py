
# from orders.models import Order
import random
import string
import pdfplumber
import pytesseract
from PIL import Image
import io
import re
import math
from statistics import stdev

def generate_order_id():
    while True:
        # Tạo mã vé 12 chữ số ngẫu nhiên
        char = string.ascii_uppercase + string.digits
        order_id = ''.join([str(random.choice(char)) for _ in range(12)])
        if not Order.objects.filter(order_id=order_id).exists():
            return order_id

def gennerate_random_string(length=6):
    char = string.ascii_uppercase + string.digits
    return ''.join([str(random.choice(char)) for _ in range(length)])

def extract_fields_from_pdf(pdf_file, form_type):
    extracted_data = {}
    text = ""
    file_name = pdf_file.name.lower()
    # Process if it's an image file
    if file_name.endswith(('.png', '.jpg', '.jpeg')):
        try:
            # Open the image file and perform OCR directly
            image = Image.open(pdf_file)
            text = pytesseract.image_to_string(image)
        except Exception as e:
            print(f"Error processing image file: {str(e)}")
            return {}  # Or handle the error as you prefer

    # Process if it's a PDF file (your existing logic)
    elif file_name.endswith('.pdf'):
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    # Use OCR for scanned image pages
                    img = page.to_image()
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    text += pytesseract.image_to_string(Image.open(img_bytes)) + "\n"
    else:
        print("Unsupported file format")
        return {}
    
    # Nhận diện các field bằng regex (unchanged code for initial extraction)
    patterns = {}
    if form_type == "form_1":
        patterns = {
            'PURCHASE CONTRACT:': r'PURCHASE CONTRACT:\s*([A-Z€0-9\-]+)',
            'Date:': r'Date:\s*([A-Za-z]+\s*\d{1,2},\s*\d{4})',
            'BUYERS:': r'BUYERS:\s*([^\n\r]+)',
            'SELLERS:': r'SELLERS:\s*([^\n\r]+)',
            'ORIGIN': r'\bORIGIN\s*:\s*([^\n\r]+)',
            'QUANTITY': r'\bQUANTITY\s*:\s*([^\n\r]+)',
            'SHIPMENT': r'\bSHIPMENT\s*:\s*([A-Za-z]+\s*\d{4})',
        }
    elif form_type == "form_2":
        patterns = {
            'Ref': r'Ref\s*([^\n\r]+)',
            'Final invoice to be raised at': r'Final invoice to be raised at\s*([^\n\r]+)',
        }
    elif form_type == "form_3":
        patterns = {
            'TO': r'TO\s*([^\n\r]+)',
            'B/L NO': r'B/L NO\s*([^\n\r]+)',
        }
    
    # Use re.search and re.IGNORECASE as before
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean up the captured group
            value = match.group(1).strip()
            if value.startswith(':'):
                 extracted_data[field] = value[1:].strip()
            else:
                 extracted_data[field] = value
        else:
            extracted_data[field] = None
          
    final_data = {}
    for field, value in extracted_data.items():
        if value is not None: # Only process non-None values, or keep all
            new_field_name = convert_field_name(field)
            if new_field_name == 'contract_date':
                value = parse_contract_date(value)

            if new_field_name == 'buyer_ref':
                value = parse_buyer_ref(value)
                
            if new_field_name == 'price':
                value = parse_price(value)
            
            if new_field_name == 'etd':
                value = parse_etd(value)

            if new_field_name == 'quantity':
                parsed = parse_quantity_field(value)
                final_data["quantity"] = parsed["quantity"]
                final_data["packing"] = parsed["packing"]
                final_data["conts_no"] = parsed["conts_no"]
            else:
                final_data[new_field_name] = value
            
    return final_data

def convert_field_name(field_name):
    field_map = {
        # form 1
        'PURCHASE CONTRACT:': 'comco_ref',
        'Date:': 'contract_date',
        'BUYERS:': 'buyers',
        'SELLERS:': 'shippers',
        'ORIGIN': 'quality',
        'QUANTITY': 'quantity',
        'SHIPMENT': 'shipment_period',
        # form 2
        'Ref': 'buyer_ref',
        'Final invoice to be raised at': 'price',
        # form 3
        'TO': 'destination',
        'B/L NO': 'etd',
    }
    return field_map.get(field_name, field_name)

def parse_quantity_field(value: str):
    result = {
        "quantity": None,
        "packing": None,
        "conts_no": None
    }
    
    if not value:
        return result
    
    # --- Lấy quantity chính ---
    # Tìm số đứng trước "MT"
    m = re.search(r'(\d+(?:[\.,]\d{3})*)\s*MT', value, re.IGNORECASE)
    if m:
        qty_str = m.group(1).replace('.', '').replace(',', '')  # bỏ dấu . hoặc ,
        try:
            result["quantity"] = int(qty_str)
        except:
            result["quantity"] = float(qty_str)
    
    # --- Lấy packing ---
    if "bulk" in value.lower():
        result["packing"] = "bulk"
    elif "jute" in value.lower():
        result["packing"] = "jute bags"
    elif "bags" in value.lower():
        result["packing"] = "bags"
    
    # --- Lấy số containers ---
    m2 = re.search(r'\((\d+)\s*containers?', value, re.IGNORECASE)
    if m2:
        result["conts_no"] = int(m2.group(1))
    
    return result

def parse_buyer_ref(value: str):
    if not value:
        return None
    m = re.search(r'/\s*(\d{6,})', value)
    return m.group(1) if m else None

def parse_price(value: str):
    if not value:
        return None
    m = re.search(r'US\$\s*([\d\.,]+)', value, re.IGNORECASE)
    return m.group(1).replace('.', '') if m else None

def parse_etd(date_str: str):
    try:
        parts = re.split(r'\s*DATE:\s*', date_str, flags=re.IGNORECASE)
        # Map các tháng viết tắt
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
            'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        # Tách các phần của ngày tháng
        parts = parts[1].upper().replace(',', '').split()
        if len(parts) == 3:
            month_abbr, day, year = parts
            month = month_map.get(month_abbr, '01')
            
            # Đảm bảo day có 2 chữ số
            day = day.zfill(2)
            
            return f"{year}-{month}-{day}"
        else:
            return None
    except Exception:
        return None

def parse_contract_date(date_str):
    try:
        # Map các tháng viết tắt
        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06',
            'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        
        # Tách các phần của ngày tháng
        parts = date_str.replace(',', '').split()
        if len(parts) == 3:
            month_abbr, day, year = parts
            month = month_map.get(month_abbr, '01')
            
            # Đảm bảo day có 2 chữ số
            day = day.zfill(2)
            
            return f"{year}-{month}-{day}"
        else:
            return None
    except Exception:
        return None

# def split_sentences(text):
#     """
#     Tách câu dựa trên dấu chấm, chấm hỏi, chấm than hoặc xuống dòng.
#     Không tách giữa số (vd: 3.75), nhưng vẫn tách nếu chấm kết thúc câu (vd: EP.4.)
#     """
#     # tách tại dấu chấm / ! / ? / ; khi sau đó là khoảng trắng + chữ hoa HOẶC hết chuỗi
#     pattern = r'(?<!\d)\.(?=\s+[A-Z]|$)|[!?;]|\n+'
#     parts = re.split(pattern, text)
#     sentences = [s.strip() for s in parts if len(s.strip()) > 5]
#     return sentences

def split_sentences(text):
    """Tách câu dựa trên dấu chấm, chấm phẩy, xuống dòng."""
    sentences = re.split(r'[.\n;!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    return sentences

def calculate_and_set_stdev(instance):
    """
    Hàm tính Standard Deviation cho 20 ngày gần nhất (Annualized)
    Công thức: STDEV.S(20 ngày) * SQRT(252)
    """
    # Lấy class của instance (OHLCDataRCDaily hoặc OHLCDataKCDaily)
    ModelClass = instance.__class__
    
    # Lấy 19 bản ghi gần nhất có ngày nhỏ hơn ngày hiện tại
    past_records = ModelClass.objects.filter(
        timestamp__lt=instance.timestamp
    ).order_by('-timestamp')[:19]

    def get_annualized_stdev(current_val, field_name):
        # Tập hợp danh sách giá trị: [giá trị hiện tại, giá trị 1, giá trị 2, ..., giá trị 19]
        values = [float(current_val)]
        for r in past_records:
            val = getattr(r, field_name)
            if val is not None:
                values.append(float(val))
        
        # STDEV.S (mẫu) yêu cầu ít nhất 2 giá trị
        if len(values) < 2:
            return 0.0
        
        # statistics.stdev tương đương STDEV.S trong Excel
        return stdev(values) * math.sqrt(252)

    # Gán giá trị vào các field tương ứng
    instance.stdev_vol_open_20_days = get_annualized_stdev(instance.volatility_open, 'volatility_open')
    instance.stdev_vol_high_20_days = get_annualized_stdev(instance.volatility_high, 'volatility_high')
    instance.stdev_vol_low_20_days = get_annualized_stdev(instance.volatility_low, 'volatility_low')
    instance.stdev_vol_close_20_days = get_annualized_stdev(instance.volatility_close, 'volatility_close')