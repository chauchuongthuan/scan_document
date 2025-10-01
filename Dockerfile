# Đặt phiên bản python như một đối số build-time
ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Tạo môi trường ảo
RUN python -m venv /opt/venv

# Đặt môi trường ảo làm vị trí hiện tại
ENV PATH=/opt/venv/bin:$PATH

# Nâng cấp pip
RUN pip install --upgrade pip

# Đặt các biến môi trường liên quan đến Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Cài đặt các phụ thuộc hệ điều hành và Tesseract-OCR
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libjpeg-dev \
    libcairo2 \
    gettext \
    curl \
    gcc \
    g++ \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-vie \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Node.js (phiên bản 20)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Tạo thư mục code của mini vm
RUN mkdir -p /app

# Đặt thư mục làm việc
WORKDIR /app

# Sao chép file requirements vào container
COPY requirements.txt /tmp/requirements.txt

# Sao chép mã dự án vào thư mục làm việc
COPY . /app

# Sao chép file env (sao chép sau cùng để tránh cache)
COPY .env.prod /app/.env

# Cài đặt các yêu cầu của dự án Python
RUN pip install -r /tmp/requirements.txt

# Thiết lập PYTHONPATH để bao gồm thư mục /app/src
ENV PYTHONPATH=/app

# Chạy các lệnh khác không cần database
RUN npm install
RUN python manage.py collectstatic --noinput

# Đặt tên dự án Django mặc định
ARG PROJ_NAME="coffee"

# Tạo script bash để chạy dự án Django
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "set -e\n\n" >> ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-7070}\"\n\n" >> ./paracord_runner.sh && \
    printf "echo \"Waiting for database...\"\n" >> ./paracord_runner.sh && \
    printf "while ! nc -z db 5432; do\n  sleep 0.1\ndone\n" >> ./paracord_runner.sh && \
    printf "echo \"Database started!\"\n" >> ./paracord_runner.sh && \
    printf "echo \"Applying database migrations...\"\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "echo \"Starting server on port \$RUN_PORT...\"\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\" --workers 3\n" >> ./paracord_runner.sh

# Làm script bash có thể chạy được
RUN chmod +x paracord_runner.sh

# Cài đặt netcat để kiểm tra database
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# Dọn dẹp bộ nhớ cache của apt để giảm kích thước image
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chạy dự án Django qua script runtime khi container khởi động
CMD ./paracord_runner.sh

EXPOSE 7070