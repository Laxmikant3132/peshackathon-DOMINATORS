@echo off
echo Starting HumanFirewall System...

:: Start Backend in a new window
start "HumanFirewall Backend" cmd /c "cd /d %~dp0backend && python main.py"

:: Start Frontend in a new window
start "HumanFirewall Frontend" cmd /c "cd /d %~dp0 && npm run dev"

echo.
echo ======================================================
echo Backend: https://humanfirewall-backend.onrender.com
echo Frontend: http://localhost:3000
echo Extension: Load from %~dp0extension
echo ======================================================
echo.
echo Keep these windows open while using the extension.
pause
