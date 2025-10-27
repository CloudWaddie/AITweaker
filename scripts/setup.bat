@echo off

REM Check for Python
python --version 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.8+ and add it to your PATH.
    goto :eof
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo Setup complete.
pause