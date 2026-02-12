import json
import requests
import os

def download_ice_csv_reports(json_file_path, output_folder="downloaded_csv"):
    base_url = "https://www.ice.com"
    
    # Tạo thư mục lưu file nếu chưa có
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Đọc file JSON
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc file JSON: {e}")
        return

    rows = data.get("datasets", {}).get("reports", {}).get("rows", [])
    
    success_count = 0
    failed_links = []

    print(f"Bắt đầu tải file vào thư mục: {output_folder}...")

    # Duyệt qua từng dòng trong dữ liệu
    for row in rows:
        report_list = row.get("reportList", [])
        for report in report_list:
            # Chỉ lấy những link là CSV/Excel
            if "csv" in report.get("url", "").lower():
                relative_url = report.get("url")
                full_url = base_url + relative_url
                file_name = relative_url.split('/')[-1]
                save_path = os.path.join(output_folder, file_name)

                try:
                    # Thêm User-Agent để tránh bị website chặn
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                    
                    response = requests.get(full_url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Successfully downloaded: {file_name}")
                        success_count += 1
                    else:
                        print(f"Failed ({response.status_code}): {full_url}")
                        failed_links.append({"url": full_url, "error": f"Status code {response.status_code}"})
                
                except Exception as e:
                    print(f"Error downloading {full_url}: {e}")
                    failed_links.append({"url": full_url, "error": str(e)})

    # Tổng kết kết quả
    print("\n--- TỔNG KẾT ---")
    print(f"Tải thành công: {success_count} file.")
    print(f"Thất bại: {len(failed_links)} file.")

    if failed_links:
        print("\nDanh sách các link bị lỗi:")
        for item in failed_links:
            print(f"- {item['url']} | Lỗi: {item['error']}")
            
    return failed_links

# Chạy function
if __name__ == "__main__":
    # Đảm bảo file 'ketqua.json' nằm cùng thư mục với file python này
    errors = download_ice_csv_reports(r"D:\PER_WORKSPACE\scan_document\media\stock_rc_summary_link.json")