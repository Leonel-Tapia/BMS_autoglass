@echo off
echo =============================================
echo  DEPLOYING CHANGES TO GITHUB AND RAILWAY
echo  BMS Autoglass / C:\BMS_autoglass
echo =============================================
echo.
git status
echo.
echo WARNING: This will commit ALL staged files.
echo Make sure you already ran: git add archivo1, git add archivo2, etc.
echo.
echo Continue with commit + push? (Y/N)
set /p respuesta=
if /i "%respuesta%"=="Y" (
    git commit -m "Automatic deployment"
    git push
    echo.
    echo [OK] Changes pushed to GitHub
    echo [OK] Railway will deploy in 2-3 minutes
) else (
    echo [CANCELLED]
)
pause