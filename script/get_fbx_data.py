import json
import pandas as pd
import os


def create_excel_from_fbx_json(json_input, output_file="data_fbx.xlsx"):
    """Tạo file Excel từ dữ liệu JSON Freightos Baltic Index (FBX).

    Parameters:
    - json_input: Đường dẫn tới file JSON (.json), chuỗi JSON string, hoặc
    dictionary.
    - output_file: Tên file Excel đầu ra (mặc định: 'data_fbx.xlsx').
    """
    # 1. Xử lý đầu vào (File path, JSON string hoặc Dictionary)
    if isinstance(json_input, str):
        if json_input.endswith(".json"):
            with open(json_input, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(json_input)
    elif isinstance(json_input, dict):
        data = json_input
    else:
        raise ValueError(
            "Đầu vào phải là đường dẫn file JSON, chuỗi JSON hoặc dict."
        )

    # 2. Lấy danh sách data từ field 'indexPoints'
    index_points = data.get("indexPoints", [])

    # 3. Chuyển đổi thành DataFrame với 3 cột theo yêu cầu: ticker, indexDate, value
    df = pd.DataFrame(index_points)[["ticker", "indexDate", "value"]]

    # Check nếu indexDate đã tồn tại trong file output thì bỏ qua, nếu không có mới thêm vào
    if os.path.exists(output_file):
        df_existing = pd.read_excel(output_file)
        
        # lấy danh sách indexDate đã có trong file output
        existing_index_dates = set(df_existing["indexDate"].tolist())
        
        # Lọc dữ liệu input: Chỉ giữ lại các ngày CHƯA TỒN TẠI trong file output
        # Nếu ngày đã có trong file -> Bị loại bỏ khỏi danh sách thêm mới (giữ nguyên dữ liệu cũ trong file)
        df_new = df[~df["indexDate"].isin(existing_index_dates)]

        df = pd.concat([df_existing, df_new], ignore_index=True)
        
    # 4. Ghi ra file Excel bằng pandas & openpyxl
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="FBX Index Points", index=False)

        # Định dạng giao diện file Excel (tùy chọn để file đẹp hơn)
        workbook = writer.book
        worksheet = writer.sheets["FBX Index Points"]

        # Tự động căn chỉnh độ rộng các cột
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

    print(f"Đã xuất file Excel thành công: {output_file}")


files = ["data_fbx", "data_fbx01", "data_fbx02", "data_fbx03", "data_fbx04", "data_fbx11", "data_fbx12", "data_fbx13", "data_fbx14", "data_fbx21", "data_fbx22", "data_fbx24", "data_fbx26"]

for name in files:
    json_path = f"D:/PER_WORKSPACE/scan_document/media/data_fbx/{name}.json"
    excel_path = f"D:/Download/{name}.xlsx"
    create_excel_from_fbx_json(json_path, excel_path)