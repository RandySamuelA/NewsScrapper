@echo off
echo ============================================
echo   NewsScrapper - Jalankan Sekarang
echo ============================================
cd /d %~dp0
python src\main.py --run-now
pause
