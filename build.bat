@echo off
setlocal
echo ========================================================
echo Building InvisiText Standalone Windows Executable (.exe)
echo ========================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Ensure PyInstaller is available
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller not detected. Installing PyInstaller...
    pip install pyinstaller
)

:: Generate fully compliant multi-layer Windows ICO (16x16 up to 256x256)
echo [INFO] Generating compliant Windows icon (favicon.ico)...
python create_ico.py

:: Run PyInstaller build
echo [INFO] Compiling single-file windowed executable with favicon icon...
pyinstaller --noconfirm --onefile --windowed --name "InvisibleTextObfuscator" --icon "favicon.ico" --add-data "favicon.png;." --clean --exclude-module matplotlib --exclude-module numpy --exclude-module pandas --exclude-module scipy --exclude-module cv2 --exclude-module mediapipe --exclude-module playwright --exclude-module streamlit --exclude-module uvicorn --exclude-module pyarrow --exclude-module reportlab --exclude-module plotly main.py

if %errorlevel% neq 0 (
    echo [ERROR] Compilation failed.
    pause
    exit /b %errorlevel%
)

echo ========================================================
echo Build Successful!
echo Executable: dist\InvisibleTextObfuscator.exe
echo ========================================================
endlocal
