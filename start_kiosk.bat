@echo off
title E-PRINT Kiosk Launcher
echo ===================================================
echo             E-PRINT KIOSK SYSTEM LAUNCHER
echo ===================================================
echo.
echo [1/3] Starting Flask backend server...
start /min cmd /c "python app.py"

echo [2/3] Waiting for server to initialize (3 seconds)...
timeout /t 3 /nobreak > nul

echo [3/3] Launching touchscreen kiosk display...
:: Try launching Chrome in app/fullscreen mode
start chrome --app="http://localhost:5000" --start-fullscreen --disable-pinch --overscroll-history-navigation=0

:: Fallback in case chrome start fails (opens default browser)
if %errorlevel% neq 0 (
    echo Chrome not found, launching default browser...
    start http://localhost:5000
)

echo.
echo ===================================================
echo Kiosk started successfully. 
echo - To close the system: Close the browser and the terminal.
echo ===================================================
pause
