# update_training_data.py
import pandas as pd
import numpy as np
import os
import sys

def add_actual_price_to_dataset(date_str, actual_price, csv_path='training_data.csv'):
    """
    Cập nhật giá thực tế vào dataset dựa trên ngày
    """
    try:
        # Đọc dữ liệu hiện tại
        df = pd.read_csv(csv_path)
        
        # Kiểm tra nếu ngày đã tồn tại
        if date_str in df['Date'].values:
            # Cập nhật Target_Price cho dòng có Date trùng
            df.loc[df['Date'] == date_str, 'Target_Price'] = actual_price
            print(f"✓ Đã cập nhật giá thực tế {actual_price} cho ngày {date_str}")
        else:
            # Tìm dòng trống gần nhất để thêm
            # Thông thường dòng cuối cùng sẽ là dòng dự đoán của hôm nay
            last_index = len(df) - 1
            
            # Tìm từ cuối lên để tìm dòng có Target_Price trống
            for i in range(last_index, max(0, last_index-10), -1):
                if pd.isna(df.at[i, 'Target_Price']):
                    df.at[i, 'Target_Price'] = actual_price
                    print(f"✓ Đã thêm giá thực tế {actual_price} vào dòng {i+1} (ngày {df.at[i, 'Date']})")
                    break
            else:
                print("⚠ Không tìm thấy dòng trống để cập nhật. Có thể thêm dòng mới?")
                
                # Thêm dòng mới với dữ liệu gần nhất
                if last_index >= 0:
                    new_row = df.iloc[last_index].copy()
                    new_row['Date'] = date_str
                    new_row['Target_Price'] = actual_price
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    print(f"✓ Đã thêm dòng mới cho ngày {date_str}")
        
        # Sắp xếp lại theo ngày
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        df = df.sort_values('Date')
        df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')
        
        # Lưu lại file
        df.to_csv(csv_path, index=False)
        print(f"✓ Đã lưu file {csv_path}")
        
        # Hiển thị thống kê
        total_rows = len(df)
        missing_target = df['Target_Price'].isna().sum()
        print(f"\n📊 Thống kê dataset:")
        print(f"   - Tổng số dòng: {total_rows}")
        print(f"   - Dòng thiếu Target_Price: {missing_target}")
        print(f"   - Hoàn thành: {((total_rows - missing_target) / total_rows * 100):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật: {e}")
        return False

def update_full_record(date_str, prev_open, prev_high, prev_low, prev_close,
                      inventory_level, weather_score, entropy_score,
                      actual_price, csv_path='training_data.csv'):
    """
    Cập nhật toàn bộ bản ghi mới (cho trường hợp đầy đủ dữ liệu)
    """
    try:
        # Đọc dữ liệu hiện tại
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(columns=['Date', 'Prev_Open', 'Prev_High', 'Prev_Low', 
                                       'Prev_Close', 'Inventory_Level', 'Weather_Score', 
                                       'Entropy_Score', 'Target_Price'])
        
        # Tạo dòng mới
        new_row = {
            'Date': date_str,
            'Prev_Open': prev_open,
            'Prev_High': prev_high,
            'Prev_Low': prev_low,
            'Prev_Close': prev_close,
            'Inventory_Level': inventory_level,
            'Weather_Score': weather_score,
            'Entropy_Score': entropy_score,
            'Target_Price': actual_price
        }
        
        # Kiểm tra nếu ngày đã tồn tại
        if date_str in df['Date'].values:
            # Cập nhật
            idx = df[df['Date'] == date_str].index[0]
            for col, val in new_row.items():
                df.at[idx, col] = val
            print(f"✓ Đã cập nhật dữ liệu cho ngày {date_str}")
        else:
            # Thêm mới
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            print(f"✓ Đã thêm dữ liệu mới cho ngày {date_str}")
        
        # Sắp xếp lại theo ngày
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        df = df.sort_values('Date')
        df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')
        
        # Lưu lại file
        df.to_csv(csv_path, index=False)
        print(f"✓ Đã lưu file {csv_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("CẬP NHẬT DỮ LIỆU HUẤN LUYỆN")
    print("=" * 50)
    
    if len(sys.argv) < 3:
        print("""Cách sử dụng:
        1. Chỉ cập nhật giá thực tế:
           python update_training_data.py <ngày> <giá_thực_tế>
           Ví dụ: python update_training_data.py 15/12/2025 372.5
        
        2. Cập nhật toàn bộ bản ghi:
           python update_training_data.py full <ngày> <prev_open> <prev_high> <prev_low> <prev_close> <inventory> <weather_score> <entropy> <actual_price>
           Ví dụ: python update_training_data.py full 16/12/2025 375.15 378.95 368.2 369.3 421379 6.5 0.85 372.5
        """)
        sys.exit(1)
    
    if sys.argv[1] == 'full':
        if len(sys.argv) != 11:
            print("⚠ Thiếu tham số! Cần 10 tham số cho chế độ full")
            sys.exit(1)
        
        update_full_record(
            date_str=sys.argv[2],
            prev_open=float(sys.argv[3]),
            prev_high=float(sys.argv[4]),
            prev_low=float(sys.argv[5]),
            prev_close=float(sys.argv[6]),
            inventory_level=float(sys.argv[7]),
            weather_score=float(sys.argv[8]),
            entropy_score=float(sys.argv[9]),
            actual_price=float(sys.argv[10])
        )
    else:
        if len(sys.argv) != 3:
            print("⚠ Thiếu tham số! Cần 2 tham số")
            sys.exit(1)
        
        add_actual_price_to_dataset(sys.argv[1], float(sys.argv[2]))
    
    print("\n" + "=" * 50)
    print("HOÀN TẤT!")
    print("=" * 50)