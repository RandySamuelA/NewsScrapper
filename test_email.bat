@echo off
echo ============================================
echo   NewsScrapper - Test Email
echo ============================================
cd /d %~dp0
python src\main.py --test-email
pause
