@echo off
echo ========================================
echo DAILY UPDATE SCRIPT - COFFEE FORECASTING
echo ========================================
echo.

REM 1. Cập nhật giá thực tế của NGÀY HÔM QUA
echo [1/3] Cập nhật giá thực tế hôm qua...
python forecasting/update_training_data.py 15/12/2025 372.5
echo.

REM 2. Retrain model với dữ liệu mới
echo [2/3] Huấn luyện lại model...
python forecasting/train_model.py
echo.

REM 3. Kiểm tra model mới
echo [3/3] Kiểm tra model...
echo Model đã được cập nhật với dữ liệu mới
echo Sẵn sàng cho dự đoán ngày mai
echo.

pause