@echo off
setlocal ENABLEDELAYEDEXPANSION

REM ==========================================
REM Watermark Studio - Windows build script
REM ==========================================

echo Starting build process...

set "PY_EXE="

REM --- Prefer your known Python path if available ---
if not defined PYTHON_EXE (
    if exist "D:\tool\Python\python.exe" (
        set "PYTHON_EXE=D:\tool\Python\python.exe"
        echo Found Python at D:\tool\Python\python.exe
    )
)

REM --- Find Python ---
if defined PYTHON_EXE (
    if exist "%PYTHON_EXE%" (
        set "PY_EXE=%PYTHON_EXE%"
        echo Found Python via PYTHON_EXE variable.
    )
)

if not defined PY_EXE (
    for /f "delims=" %%i in ('where python 2^>NUL') do (
        echo "%%i" | find /i "WindowsApps" >NUL || (
            if not defined PY_EXE set "PY_EXE=%%i"
        )
    )
    if defined PY_EXE (
        echo Found Python on PATH.
    )
)

if not defined PY_EXE (
    where py >NUL 2>&1 && (
        py -3 -c "import sys" >NUL 2>&1 && (
            set "PY_EXE=py -3"
            echo Found Python via py launcher.
        )
    )
)

if not defined PY_EXE (
    echo [ERROR] Python 3 not found. Please install Python 3 and add it to your PATH.
    exit /b 1
)

echo Using Python: %PY_EXE%

REM --- Create venv and install dependencies ---
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    %PY_EXE% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"

REM Print versions
"%VENV_PY%" -c "import sys; print('Python', sys.version)"
"%VENV_PY%" -m pip --version

REM Ensure modern pip/setuptools/wheel, then install from wheels only
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip/setuptools/wheel.
    exit /b 1
)

REM Prefer binary wheels to avoid building from source
"%VENV_PY%" -m pip install --only-binary=:all: --upgrade -r requirements.txt
if errorlevel 1 (
    echo [WARN] Binary-only install failed. Retrying with prefer-binary...
    "%VENV_PY%" -m pip install --prefer-binary --upgrade -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        exit /b 1
    )
)

REM --- Build with PyInstaller ---
echo Building executable...
"%VENV_PY%" -m PyInstaller --noconsole --name WatermarkStudio --clean ^
  --collect-submodules PIL --collect-data PIL ^
  --collect-submodules PyQt5 --collect-data PyQt5 --hidden-import PyQt5.sip ^
  --add-data "app/templates.json;app" app/main.py

if exist "dist\WatermarkStudio\WatermarkStudio.exe" (
    echo.
    echo Build successful!
    echo Executable is at: %CD%\dist\WatermarkStudio\WatermarkStudio.exe
) else (
    echo [ERROR] Build failed. Check PyInstaller output above.
    exit /b 1
)

endlocal
