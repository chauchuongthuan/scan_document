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

# Cài đặt các phụ thuộc hệ điều hành
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libjpeg-dev \
    libcairo2 \
    gettext \
    curl \
    gcc \
    g++ \
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

# Sử dụng khi deploy dxup
COPY .env.prod /app/.env

# Sao chép mã dự án vào thư mục làm việc
COPY . /app

# Cài đặt các yêu cầu của dự án Python
RUN pip install -r /tmp/requirements.txt

# Thiết lập PYTHONPATH để bao gồm thư mục /app/src
ENV PYTHONPATH=/app

ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

# Chạy các lệnh khác không cần database
#RUN python src/manage.py vendor_pull
RUN npm install
# RUN npm run build
RUN python manage.py collectstatic --noinput

# Đặt tên dự án Django mặc định
ARG PROJ_NAME="coffee"

# Tạo script bash để chạy dự án Django
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-7070}\"\n\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./paracord_runner.sh

# Làm script bash có thể chạy được
RUN chmod +x paracord_runner.sh

# Dọn dẹp bộ nhớ cache của apt để giảm kích thước image
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chạy dự án Django qua script runtime khi container khởi động
CMD ./paracord_runner.sh

EXPOSE 7070
