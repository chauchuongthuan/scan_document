from datetime import datetime
import pandas as pd
from django.conf import settings
from bs4 import BeautifulSoup

# Định nghĩa thư mục chứa các file Robusta đã được tải về
# Bạn cần đảm bảo thư mục này tồn tại và có thể truy cập được
def get_open_interest_from_html_file():
    try:
        input_file = 'D:/PER_WORKSPACE/scan_document/media/open_interest/open_interest_kc.html'
        output_file = 'D:/PER_WORKSPACE/scan_document/media/open_interest/open_interest_kc.xlsx'
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = f.read()
        
        soup = BeautifulSoup(data, 'html.parser')
        rows = soup.find_all('tr')
        
        data_list = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                date_str = cols[0].text.strip()
                # Convert date from "Month day, Year" to "dd/mm/yyyy"
                date_obj = datetime.strptime(date_str, '%B %d, %Y')
                formatted_date = date_obj.strftime('%d/%m/%Y')
                open_interest = float(cols[1].text.strip().replace(',', ''))
                data_list.append([formatted_date, open_interest])
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(data_list, columns=['Date', 'Open Interest'])
        df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    get_open_interest_from_html_file()