@echo off
echo === Bat dau thiet lap moi truong Django & Node.js ===

REM Kiem tra Python
python --version 2>NUL
if errorlevel 1 (
    echo ERROR: Python chua duoc cai dat. Vui long cai dat Python truoc.
    exit /b 1
)

REM Kiem tra Node.js
node --version 2>NUL
if errorlevel 1 (
    echo WARNING: Node.js chua duoc cai dat.
    echo Vui long cai dat Node.js 20 tu: https://nodejs.org/
    echo Sau khi cai dat, chay lai script nay.
    pause
    exit /b 1
)

REM Kiem tra phien ban Node.js
for /f "tokens=2 delims=." %%I in ('node --version') do (
    if %%I LSS 20 (
        echo WARNING: Can nang cap Node.js len phien ban 20
        echo Vui long cai dat Node.js 20 tu: https://nodejs.org/
        pause
        exit /b 1
    )
)

REM 1. Tao moi truong ao Python
echo 1. Dang tao moi truong ao Python...
python -m venv venv

REM 2. Kich hoat moi truong ao
echo 2. Dang kich hoat moi truong ao...
call venv\Scripts\activate.bat

REM 3. Cai dat cac package Python
echo 3. Dang cai dat cac package Python...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo WARNING: File requirements.txt khong ton tai.
    echo Tao file requirements.txt mau voi cac package co ban...
    (
        echo django==5.0.1
        echo djangorestframework==3.14.0
        echo python-dotenv==1.0.0
        echo pillow==10.2.0
        echo psycopg2-binary==2.9.9
        echo django-cors-headers==4.3.1
    ) > requirements.txt
    pip install -r requirements.txt
)

REM 4. Cai dat cac package npm
echo 4. Dang cai dat cac package npm...
if exist package.json (
    call npm install
) else (
    echo WARNING: File package.json khong ton tai.
    echo Khoi tao project npm...
    call npm init -y

    echo Cai dat cac package npm co ban...
    call npm install react react-dom @babel/core @babel/preset-react @babel/preset-env
)

REM Kiem tra cai dat Django
python -c "import django"
if errorlevel 1 (
    echo ERROR: Cai dat Django that bai.
    exit /b 1
)

echo.
echo === Thiet lap hoan tat ===
echo Moi truong ao Python da duoc tao va kich hoat
echo Cac package Python da duoc cai dat
echo Node.js da san sang
echo Cac package npm da duoc cai dat
echo.
echo De bat dau lam viec:
echo 1. Moi truong ao da duoc kich hoat
echo 2. Kiem tra Django: python -m django --version
echo 3. Kiem tra Node: node --version
echo 4. Tao project moi: django-admin startproject your_project_name

pause
