#!/bin/bash

# File setup.sh
echo "=== Bắt đầu thiết lập môi trường Django & Node.js ==="

# Kiểm tra Python đã được cài đặt chưa
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python chưa được cài đặt. Vui lòng cài đặt Python trước."
    exit 1
fi

# Kiểm tra Node.js và npm
if ! command -v node &> /dev/null; then
    echo "WARNING: Node.js chưa được cài đặt. Đang cài đặt Node.js 20..."

    # Cài đặt NVM (Node Version Manager)
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

    # Load NVM
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    # Cài đặt Node.js 20
    nvm install 20
    nvm use 20

    echo "Node.js đã được cài đặt thành công!"
fi

# 1. Tạo môi trường ảo Python
echo "1. Đang tạo môi trường ảo Python..."
python3 -m venv venv

# 2. Kích hoạt môi trường ảo
echo "2. Đang kích hoạt môi trường ảo..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# 3. Cài đặt các package Python từ requirements.txt
echo "3. Đang cài đặt các package Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "WARNING: File requirements.txt không tồn tại."
    echo "Tạo file requirements.txt mẫu với các package cơ bản..."
    echo "django==5.0.1
djangorestframework==3.14.0
python-dotenv==1.0.0
pillow==10.2.0
psycopg2-binary==2.9.9
django-cors-headers==4.3.1" > requirements.txt
    pip install -r requirements.txt
fi

# 4. Cài đặt các package npm
echo "4. Đang cài đặt các package npm..."
if [ -f "package.json" ]; then
    npm install
else
    echo "WARNING: File package.json không tồn tại."
    echo "Khởi tạo project npm..."
    npm init -y

    # Cài đặt một số package phổ biến
    echo "Cài đặt các package npm cơ bản..."
    npm install react react-dom @babel/core @babel/preset-react @babel/preset-env
fi

# Kiểm tra cài đặt Django
if python -c "import django" &> /dev/null; then
    echo "=== Cài đặt Django thành công! ==="
else
    echo "ERROR: Cài đặt Django thất bại."
    exit 1
fi

echo "
=== Thiết lập hoàn tất ===
Môi trường ảo Python đã được tạo và kích hoạt
Các package Python đã được cài đặt
Node.js 20 đã được cài đặt
Các package npm đã được cài đặt

Để bắt đầu làm việc:
1. Môi trường ảo đã được kích hoạt
2. Kiểm tra Django: python -m django --version
3. Kiểm tra Node: node --version
4. Tạo project mới: django-admin startproject your_project_name
"
