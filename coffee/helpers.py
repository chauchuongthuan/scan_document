
# from orders.models import Order
import random
import string
import pdfplumber
import pytesseract
from PIL import Image
import io
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
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

def extract_fields_from_pdf(pdf_file):
    extracted_data = {}
    text = ""
    
    # Xử lý PDF bằng pdfplumber (unchanged code for text extraction)
    import pdfplumber
    import io
    from PIL import Image
    import pytesseract
    import re
    # Assuming convert_date_format and other necessary imports are available
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Thử trích xuất văn bản trực tiếp
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            else:
                # Nếu không có text, sử dụng OCR cho ảnh
                img = page.to_image()
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                # NOTE: pytesseract and PIL must be imported/available
                text += pytesseract.image_to_string(Image.open(img_bytes)) + "\n"
    
    # Nhận diện các field bằng regex (unchanged code for initial extraction)
    patterns = {
        'THE BUYER': r'THE BUYER\s*([^\n\r]+)', # Added \s* to handle potential spaces
        'CONTRACT NO': r'CONTRACT NO\s*([^\n\r]+)', # Added \s*
        'B/L NO': r'B/L NO\s*([^\n\r]+)', # Added \s*
        'FROM': r'FROM\s*([^\n\r]+)', # Added \s*
        'TO': r'TO\s*([^\n\r]+)', # Added \s*
        'Final invoice to be raised at': r'Final invoice to be raised at\s*([^\n\r]+)', # Added \s*
    }
    
    # Use re.search and re.IGNORECASE as before
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean up the captured group
            value = match.group(1).strip()
            # The regex r'HEADER*([^\n\r]+)' is likely missing spaces/delimiters. 
            # I've modified the pattern above to r'HEADER\s*([^\n\r]+)'.
            # If the header is followed by a colon and then data, adjust the pattern:
            # e.g., r'THE BUYER:\s*([^\n\r]+)'
            if value.startswith(':'):
                 extracted_data[field] = value[1:].strip()
            else:
                 extracted_data[field] = value
        else:
            extracted_data[field] = None
    
    # Tách contract_no và date (unchanged code for contract processing)
    # The original code used 'CONTRACT_NO' but the initial extraction used 'CONTRACT NO' 
    # and the patterns dictionary uses 'CONTRACT NO'. 
    # I'll correct the following block to use 'CONTRACT NO'.
    if extracted_data.get('CONTRACT NO'):
        contract_field = extracted_data['CONTRACT NO']
        
        # Tách contract_no và date từ chuỗi ": C21257-04 DATE: APR 10, 2025"
        contract_parts = re.split(r'\s*DATE:\s*', contract_field, flags=re.IGNORECASE)
        
        if len(contract_parts) >= 2:
            # Lấy contract_no (bỏ dấu : ở đầu nếu có)
            contract_no = contract_parts[0].strip()
            if contract_no.startswith(':'):
                contract_no = contract_no[1:].strip()
            
            # Lấy và chuyển đổi ngày tháng
            date_str = contract_parts[1].strip()
            
            extracted_data['CONTRACT NO'] = contract_no
            # NOTE: 'CONTRACT DATE' is a new key, which is fine here because it's after iteration
            # BUT for consistency with the field mapping, let's use the field mapping key
            extracted_data['CONTRACT DATE'] = convert_date_format(date_str) # Assuming convert_date_format is defined
        else:
            # Nếu không tách được, giữ nguyên và để contract_date là None
            extracted_data['CONTRACT DATE'] = None
            
    final_data = {}
    for field, value in extracted_data.items():
        if value is not None: # Only process non-None values, or keep all
            new_field_name = convert_field_name(field)
            # Use the new field name as the key in the NEW dictionary
            final_data[new_field_name] = value
            
    return final_data

# The supporting function is correct
def convert_field_name(field_name):
    field_map = {
        'THE BUYER': 'buyers',
        'CONTRACT NO': 'comco_ref',
        'CONTRACT DATE': 'contract_date',
        'B/L NO': 'buyer_ref',
        'FROM': 'from',
        'TO': 'to',
        'Final invoice to be raised at': 'price',
    }
    return field_map.get(field_name, field_name)
def convert_date_format(date_str):
    """
    Chuyển đổi chuỗi ngày tháng từ dạng 'APR 10, 2025' sang 'YYYY-MM-DD'
    """
    try:
        # Map các tháng viết tắt
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
            'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        # Tách các phần của ngày tháng
        parts = date_str.upper().replace(',', '').split()
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