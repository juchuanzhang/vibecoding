@echo off
echo ========================================
echo   象棋分析器 - 启动HTTP服务器
echo ========================================
echo.
echo 请在浏览器中访问: http://localhost:8080
echo.
echo 注意: 不能直接双击 index.html 打开
echo       必须通过HTTP服务器访问才能加载WASM引擎
echo.
echo 按Ctrl+C停止服务器
echo ========================================
echo.
python -m http.server 8080