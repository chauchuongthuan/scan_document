from django.http import JsonResponse
from django.shortcuts import render
import os
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.conf import settings
from rapidfuzz import fuzz, process
# Keyword Views
class KeywordListView:  
    @login_required(login_url="login_cms")
    def keyword(request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            try:
                excel_file = request.FILES['excel_file']
                
                # Danh sách từ khóa fitting với các biến thể
                fitting_keywords = [
                    'restaurant', 'coffee', 'cafe', 'quán ăn', 'nhà hàng',
                    'nha hang', 'quan an', 'quận 1', 'quan 1',
                    'food', 'drink', 'đồ uống', 'thức ăn', 'menu', 'cf', 'cà phê', 
                    'cơm gà', 'brunch', 'caphe', 'muối', 'muoi', 'café', 'ca phe'
                ]
                
                # Từ khóa loại trừ (chứa từ này sẽ bị loại khỏi matched)
                exclude_keywords = [
                    'quận 10', 'quan 10', 'lý thái tổ', 'ly thai to',
                    'quận 2', 'quan 2', 'quận 3', 'quan 3', 'quận 4', 'quan 4',
                    'quận 5', 'quan 5', 'quận 6', 'quan 6', 'quận 7', 'quan 7',
                    'quận 8', 'quan 8', 'quận 9', 'quan 9', 'quận 11', 'quan 11',
                    'quận 12', 'quan 12', 'q10', 'q2', 'q3', 'q4', 'q5', 'q7', 'gò vấp',
                    'thủ đức', 'thu duc', 'tân phú', 'tan phu', 'phú mỹ hưng', 'phu my hung',
                    'hà nội', 'ha noi', 'đà nẵng', 'da nang', 'vung tau', 'vũng tàu',
                    'tân bình', 'tan binh', 'hóc môn', 'hoc mon'
                ]

                temp_file_path = default_storage.save('temp/' + excel_file.name, excel_file)
                file_path = os.path.join(default_storage.location, temp_file_path)

                # Đọc file Excel
                df = pd.read_excel(file_path, header=2)
                
                # Kiểm tra cột tồn tại
                if 'Cụm từ tìm kiếm' not in df.columns:
                    os.remove(file_path)
                    return JsonResponse({
                        'status': 'error',
                        'message': 'File Excel không có cột "Cụm từ tìm kiếm"'
                    }, status=400)

                mask = ~df['Cụm từ tìm kiếm'].astype(str).str.startswith('Tổng số:')
                df = df[mask]
                
                # Nếu DataFrame rỗng sau khi lọc
                if df.empty:
                    os.remove(file_path)
                    return JsonResponse({
                        'status': 'error',
                        'message': 'File không có dữ liệu sau khi lọc các dòng tổng số'
                    }, status=400)
                
                df_work = df.copy()
                df_work['Phân loại'] = 'Không phù hợp'
                
                def advanced_keyword_check(text):
                    if pd.isna(text):
                        return 'Không phù hợp'
                    
                    text_lower = str(text).lower()
                    
                    # Kiểm tra từ khóa loại trừ trước
                    for exclude_keyword in exclude_keywords:
                        if exclude_keyword.lower() in text_lower:
                            return 'Không phù hợp'  # Bị loại trừ -> cho vào unmatched
                    
                    # Kiểm tra khớp chính xác
                    for keyword in fitting_keywords:
                        if keyword.lower() in text_lower:
                            return 'Phù hợp'
                    
                    # Kiểm tra khớp gần đúng cho các từ dễ sai chính tả
                    coffee_variations = ['coffee', 'coffe', 'cofee', 'cafe', 'caphe', 'café']
                    for coffee_var in coffee_variations:
                        if coffee_var in text_lower and fuzz.partial_ratio(coffee_var, text_lower) > 80:
                            # Kiểm tra thêm xem có phải là biến thể của coffee không
                            best_match, score, _ = process.extractOne(text_lower, coffee_variations)
                            if score > 75:
                                return 'Phù hợp'
                    
                    return 'Không phù hợp'

                # Áp dụng phân loại
                df_work['Phân loại'] = df_work['Cụm từ tìm kiếm'].apply(advanced_keyword_check)

                # Tách thành 2 DataFrame (không cần excluded riêng)
                df_matched = df_work[df_work['Phân loại'] == 'Phù hợp'].drop('Phân loại', axis=1)
                df_unmatched = df_work[df_work['Phân loại'] == 'Không phù hợp'].drop('Phân loại', axis=1)

                # Đếm số lượng excluded (cho thống kê)
                excluded_count = 0
                for index, row in df_work.iterrows():
                    if row['Phân loại'] == 'Không phù hợp':
                        text_lower = str(row['Cụm từ tìm kiếm']).lower()
                        # Kiểm tra xem có phải bị excluded không
                        for exclude_keyword in exclude_keywords:
                            if exclude_keyword.lower() in text_lower:
                                excluded_count += 1
                                break

                # Lưu file
                original_name = os.path.splitext(excel_file.name)[0]
                
                response_data = {
                    'status': 'success',
                    'message': f'Phân loại thành công! Tìm thấy {len(df_matched)} từ khóa phù hợp, {excluded_count} từ khóa bị loại trừ và {len(df_unmatched) - excluded_count} từ khóa không phù hợp.',
                    'statistics': {
                        'matched': len(df_matched),
                        'excluded': excluded_count,
                        'unmatched': len(df_unmatched) - excluded_count,
                        'total': len(df_work)
                    },
                }

                # Lưu file matched
                if len(df_matched) > 0:
                    matched_filename = f"{original_name}_phu_hop.xlsx"
                    matched_path = os.path.join(settings.MEDIA_ROOT, 'exports', matched_filename)
                    os.makedirs(os.path.dirname(matched_path), exist_ok=True)
                    df_matched.to_excel(matched_path, index=False)
                    response_data['matched_file'] = f'/media/exports/{matched_filename}'

                # Lưu file unmatched (bao gồm cả excluded và thực sự không phù hợp)
                if len(df_unmatched) > 0:
                    unmatched_filename = f"{original_name}_khong_phu_hop.xlsx"
                    unmatched_path = os.path.join(settings.MEDIA_ROOT, 'exports', unmatched_filename)
                    os.makedirs(os.path.dirname(unmatched_path), exist_ok=True)
                    df_unmatched.to_excel(unmatched_path, index=False)
                    response_data['unmatched_file'] = f'/media/exports/{unmatched_filename}'

                # Xóa file tạm
                os.remove(file_path)
                return JsonResponse(response_data)

            except Exception as e:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xử lý file: {str(e)}'
                }, status=400)
        
        return render(request, 'keywords/create.html')
    
