@echo off
chcp 65001>nul>nul
echo ========================================
echo   XiangQi Analyzer - HTTP Server
echo ========================================
echo.
echo Open browser: http://localhost:8080
echo.
echo Note: Cannot open index.html directly
echo       Must use HTTP server to load WASM engine
echo.
echo Press Ctrl+C to stop server
echo ========================================
echo.
python -m http.server 8080