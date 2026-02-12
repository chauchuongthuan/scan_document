import pandas as pd
import re

def text_to_coffee_excel_robust(raw_data, output_file="D:/PER_WORKSPACE/scan_document/media/ecf/export_ecf_2014_2019.xlsx"):
    # 1. Làm sạch dữ liệu: Bỏ tag và giữ lại cấu trúc dòng
    lines = [re.sub(r"\\s*", "", line).strip() for line in raw_data.strip().split('\n')]
    
    # Dictionary tổng để lưu trữ: data_map[Ngày][Tên_Danh_Mục] = Giá_trị
    data_map = {}
    current_dates = []
    
    # Regex để nhận diện ngày tháng (xử lý cả 31-Jan-23 và 31 Jan 23)
    date_pattern = r"\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-\s]\d{2,4}"

    for line in lines:
        if not line: continue
        
        # KIỂM TRA DÒNG TIÊU ĐỀ (Header)
        if line.startswith("Port") or line.startswith("Type of coffee"):
            # Tìm tất cả các ngày tháng có trong dòng này
            current_dates = re.findall(date_pattern, line)
            # Chuẩn hóa ngày (thay khoảng trắng bằng dấu - để thống nhất)
            current_dates = [d.replace(" ", "-") for d in current_dates]
            continue
            
        # KIỂM TRA DÒNG DỮ LIỆU
        if current_dates:
            # Tách các con số ở cuối dòng
            parts = line.split()
            # Tìm xem có bao nhiêu số (chuẩn hóa dấu chấm/phẩy trước khi kiểm tra)
            values_raw = []
            name_parts = []
            
            for p in parts:
                # Nếu là số (sau khi bỏ dấu phân tách)
                clean_p = p.replace('.', '').replace(',', '')
                if clean_p.isdigit():
                    values_raw.append(float(clean_p))
                else:
                    name_parts.append(p)
            
            category_name = " ".join(name_parts)
            
            # Khớp giá trị vào ngày tương ứng (theo thứ tự từ trái qua phải)
            for idx, val in enumerate(values_raw):
                if idx < len(current_dates):
                    target_date = current_dates[idx]
                    if target_date not in data_map:
                        data_map[target_date] = {}
                    data_map[target_date][category_name] = val

    # 2. Chuyển đổi Map thành DataFrame
    # Mỗi hàng sẽ là một Ngày, mỗi cột là một Danh mục (Port/Type)
    df = pd.DataFrame.from_dict(data_map, orient='index')
    
    # Sắp xếp lại theo thời gian để file Excel chuyên nghiệp hơn
    df.index = pd.to_datetime(df.index, format='%d-%b-%y', errors='coerce')
    df = df.sort_index()
    
    # Reset index để đưa cột Ngày vào file
    df.index.name = 'Date'
    df = df.reset_index()

    # 3. Xuất file Excel (Tự động để trống các ô thiếu dữ liệu)
    df.to_excel(output_file, index=False)
    print(f"--- Đã xử lý xong! File lưu tại: {output_file} ---")
    return df

# Chạy thử với dữ liệu của bạn
raw_input = """
Port 31-Dec-18 31-Jan-19 28-Feb-19 31 Mar 19 30-Apr-19 31-May-19 30-Jun-19
Antwerp 379.850 377.152 369.301 373.753 377.321 377.215 383.279
Hamburg 107.374 109.177 106.458 109.181 104.622 107.522 112.229
Genoa 89.790 81.243 83.716 90.636 102.752 105.380 104.896
Le Havre 27.684 27.452 26.657 27.344 28.333 28.548 31.598
Trieste 41.122 45.261 43.504 44.246 47.769 49.926 53.678
Barcelona 42.919 43.650 46.087 40.988 40.000 37.632 35.910
Total Europe 688.739 683.935 675.723 686.148 700.797 706.223 721.590

Port 31-Jul-19 31-Aug-19 30-Sep-19 31-Oct-19 30-Nov-19 31-Dec-19
Antwerp 392.992
Hamburg 121.278 133.215 129.901 125.151 117.299 105.019
Genoa 104.821 111.163 108.841 110.752 110.805 97.547
Le Havre 32.634 32.870 32.568 29.777 27.778 27.126
Trieste 55.205 58.736 56.555 54.704 53.516 54.256
Barcelona 38.671 41.837 45.449 44.660 40.574 40.205
Total Europe 745.601 377.821 373.314 365.044 349.972 324.153

Port 31-Dec-17 31-Jan-18 28-Feb-18 31 Mar 18 30-Apr-18 31-May-18 30-Jun-18
Antwerp 321.519 313.109 315.088 324.610 327.607 334.163 337.021
Hamburg 112.379 115.997 119.366 118.953 126.014 125.781 124.439
Genoa 76.015 93.268 90.001 91.875 98.090 102.857 98.935
Le Havre 28.482 28.396 26.409 24.248 26.741 26.669 28.854
Trieste 48.326 44.784 43.245 42.758 46.518 48.215 48.328
Barcelona 43.365 43.173 43.535 43.962 42.697 44.830 49.411
Total Europe 630.087 638.727 641.505 646.406 667.667 682.515 691.037

Port 31-Jul-18 31-Aug-18 30-Sep-18 31-Oct-18 30-Nov-18 31-Dec-18
Antwerp 336.510 346.648 361.538 370.277 377.973 379.850
Hamburg 121.745 122.343 122.131 115.403 105.710 107.374
Genoa 94.303 99.178 95.907 96.138 90.037 89.790
Le Havre 31.231 32.584 29.903 28.489 27.814 27.684
Trieste 45.870 47.843 47.096 44.252 41.971 41.122
Barcelona 55.197 52.700 46.793 43.875 41.853 42.919
Total Europe 684.856 701.296 703.368 698.434 685.358 688.739

Port 31-Dec-16 31-Jan-17 28-Feb-17 31 Mar 17 30-Apr-17 31-May-17 30-Jun-17
Antwerp 291.296 316.081 334.067 343.101 354.702 361.564 361.620
Hamburg 135.772 136.910 134.643 138.604 141.756 146.961 146.336
Genoa 98.619 95.587 92.688 93.070 106.488 109.531 111.386
Le Havre 34.334 34.453 31.943 33.187 31.669 31.216 33.073
Trieste 51.539 52.328 53.194 55.657 54.101 56.775 56.427
Total Europe 611.560 635.359 646.535 663.619 688.716 706.047 708.842

Port 31-Jul-17 31-Aug-17 30-Sep-17 31-Oct-17 30-Nov-17 31-Dec-17
Antwerp 362.425 364.734 354.785 337.688 325.046 321.519
Hamburg 135.810 129.016 120.244 122.966 113.237 112.379
Genoa 111.106 109.522 112.166 108.882 100.826 76.015
Le Havre 32.775 33.711 38.995 31.239 28.819 28.482
Trieste 55.619 56.982 55.268 53.658 51.673 48.326
Total Europe 697.735 693.965 681.458 654.433 619.601 586.721

Port 31-Dec-15 31-Jan-16 29-Feb-16 31 Mar 16 30-Apr-16 31-May-16 30-Jun-16
Antwerp 337.042 333.922 317.689 311.852 307.086 306.124 303.504
Bremen 103.706 103.706 103.706 103.706 103.706 103.706 103.706
Hamburg 107.451 105.717 107.560 113.629 122.014 126.750 136.089
Genoa 88.755 82.256 85.479 87.174 99.314 108.093 116.483
Le Havre 30.399 32.405 31.189 29.201 27.565 30.772 33.802
Trieste 44.260 44.081 43.454 42.141 47.105 49.236 48.559
Total Europe 711.613 702.088 689.078 687.703 706.789 724.681 742.142

Port 31-Jul-16 31-Aug-16 30-Sep-16 31-Oct-16 30-Nov-16 31-Dec-16
Antwerp 299.442 297.130 291.592 288.483 293.253 291.296
Bremen 103.706 103.706 103.706 103.706 103.706 103.706
Hamburg 135.897 126.112 121.225 122.325 130.400 135.772
Genoa 105.546 103.603 106.655 108.207 99.933 98.619
Le Havre 35.205 36.146 35.695 35.480 34.072 34.334
Trieste 49.277 50.072 48.906 47.291 48.905 51.539
Total Europe 729.073 716.770 707.779 705.492 710.270 715.266

Port 31-Dec-14 31-Jan-15 28-Feb-15 31 Mar 15 30-Apr-15 31-May-15 30-Jun-15
Antwerp 363.040 365.732 374.113 373.092 368.520 393.851 366.034
Bremen 77.410 79.404 78.574 77.867 79.946 83.554 86.761
Hamburg 109.791 110.233 109.954 107.932 115.140 114.963 112.023
Genoa 62.525 63.572 63.572 63.572 63.572 63.572 63.572
Le Havre 29.931 32.405 29.700 29.220 28.668 28.965 32.062
Trieste 46.749 43.886 42.350 43.758 41.478 41.410 43.214
Total Europe 689.446 695.233 698.263 695.441 697.324 726.315 703.666

Port 31-Jul-15 31-Aug-15 30-Sep-15 31-Oct-15 30-Nov-15 31-Dec-15
Antwerp 367.254 361.557 357.510 346.262 350.107 337.042
Bremen 89.850 98.692 103.706 103.706 103.706 103.706
Hamburg 118.805 120.384 115.993 113.037 105.987 107.451
Genoa 63.572 63.572 63.572 81.807 77.262 88.755
Le Havre 33.231 33.073 31.664 31.294 28.842 30.399
Trieste 41.854 43.060 43.060 35.038 42.522 44.260
Total Europe 714.566 720.339 715.505 711.144 708.426 711.613

Port 31-Dec-13 31-Jan-14 28-Feb-14 31-Mar-14 30 Apr 14 31-May-14 30-Jun-14
Antwerp 4.072.550 3.980.000 3.904.400 3.899.283 4.191.067 4.803.250 5.045.983
Bremen 983.833 1.041.700 975.100 998.117 1.166.717 1.280.283 1.517.083
Hamburg 1.651.783 1.626.017 1.609.433 1.506.900 1.622.967 1.801.300 1.934.317
Genoa 936.653 937.926 977.152 1.037.386 1.225.721 1.361.827 1.422.710
Le Havre 437.717 491.567 418.950 435.817 459.417 482.817 493.467
Trieste 678.642 655.981 683.604 690.263 707.225 734.078 670.007
Total Europe 8.761.178 8.731.917 8.528.140 8.567.766 9.373.113 10.463.555 11.083.567

Port 31-Jul-14 31-Aug-14 30-Sep-14 31-Oct-14 30-Nov-14 31-Dec-14
Antwerp 5.417.900 5.414.050 5.832.083 5.879.467 5.898.334 6.050.659
Bremen 1.589.217 1.637.883 1.600.433 1.517.633 1.420.067 1.290.167
Hamburg 2.004.517 1.976.217 1.964.467 1.907.217 1.829.417 1.829.850
Genoa 1.356.906 1.524.125 1.398.032 1.249.058 1.111.355 1.042.090
Le Havre 500.667 557.167 545.467 499.733 495.483 498.850
Trieste 717.020 771.202 754.170 711.951 718.526 779.155
Total Europe 11.586.226 11.880.644 12.094.652 11.765.059 11.473.181 11.490.771

"""
df_result = text_to_coffee_excel_robust(raw_input)