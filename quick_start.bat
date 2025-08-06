@echo off
REM Quick start script for SonarResolve - works with or without Poetry

echo ====================================
echo    SonarResolve Quick Start
echo ====================================
echo.

REM Check if Poetry is available
poetry --version >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Poetry detected - using Poetry workflow
    goto poetry_workflow
) else (
    echo [INFO] Poetry not found - using traditional pip workflow
    goto pip_workflow
)

:poetry_workflow
echo.
echo Step 1: Installing dependencies with Poetry...
poetry install
if %errorlevel% neq 0 (
    echo [ERROR] Poetry install failed
    goto fallback_to_pip
)

echo.
echo Step 2: Testing connections...
poetry run python test_connections.py
if %errorlevel% neq 0 (
    echo [ERROR] Connection test failed
    echo Please check your .env configuration
    pause
    exit /b 1
)

echo.
echo ✓ Setup complete! You can now use:
echo   - poetry run python main.py          (Create Jira tasks)
echo   - poetry run python auto_fix.py      (Auto-fix with AI)
echo   - make.bat [command]                  (Use helper commands)
echo.
pause
exit /b 0

:fallback_to_pip
echo [WARNING] Falling back to pip installation...

:pip_workflow
echo.
echo Step 1: Checking if Python is available...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

echo.
echo Step 2: Creating virtual environment...
if not exist venv (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Step 3: Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

REM Check if requirements.txt exists, if not create it from pyproject.toml
if not exist requirements.txt (
    echo [INFO] Creating requirements.txt from pyproject.toml...
    echo requests==2.31.0 > requirements.txt
    echo jira==3.5.0 >> requirements.txt
    echo python-dotenv==1.0.0 >> requirements.txt
    echo pydantic==2.5.0 >> requirements.txt
    echo GitPython==3.1.40 >> requirements.txt
    echo openai==1.3.0 >> requirements.txt
    echo anthropic==0.7.0 >> requirements.txt
    echo python-gitlab==4.1.0 >> requirements.txt
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 4: Testing connections...
python test_connections.py
if %errorlevel% neq 0 (
    echo [ERROR] Connection test failed
    echo Please check your .env configuration
    pause
    exit /b 1
)

echo.
echo ✓ Setup complete! You can now use:
echo   - python main.py          (Create Jira tasks)
echo   - python auto_fix.py      (Auto-fix with AI)
echo.
echo Note: Always activate the virtual environment first:
echo   venv\Scripts\activate.bat
echo.
pause
exit /b 0
