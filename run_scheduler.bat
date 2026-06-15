@echo off
echo ============================================
echo   NewsScrapper - Scheduler Harian
echo   Kirim email setiap pagi otomatis
echo   Tekan Ctrl+C untuk berhenti
echo ============================================
cd /d %~dp0
python src\main.py --schedule
pause
