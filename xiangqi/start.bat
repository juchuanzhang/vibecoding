@echo off
chcp 65001 >nul
echo ========================================
echo   XiangQi Analyzer - HTTP Server
echo ========================================
echo.
echo   Open in browser: http://localhost:8080
echo.
echo   Press Ctrl+C to stop
echo ========================================
echo.
python -m http.server 8080