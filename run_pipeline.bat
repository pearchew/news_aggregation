@echo off
echo ===================================================
echo Starting Autonomous Tech News & Trends Aggregator...
echo ===================================================

:: Check if the virtual environment exists
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found in the 'venv' folder.
    echo Please follow the README instructions to set it up first.
    pause
    exit /b
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Run the main pipeline orchestrator
python main.py

:: Deactivate the environment once finished
deactivate

echo.
echo Pipeline finished.
pause