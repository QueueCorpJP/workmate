@echo off
echo ===================================================
echo Running Supabase Setup Script
echo ===================================================
echo.
echo This script will create the necessary database tables and functions in your Supabase project.
echo.
echo Make sure you have updated your .env file with the correct Supabase credentials:
echo  - SUPABASE_URL
echo  - SUPABASE_KEY
echo  - DB_HOST
echo  - DB_USER
echo  - DB_PASSWORD
echo  - DB_NAME
echo  - DB_PORT
echo.
echo Press any key to continue...
pause > nul

cd Chatbot-backend-main
python setup_supabase.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo Setup completed successfully!
) else (
    echo Setup failed. Please check the error messages above.
)
echo.
echo Press any key to exit...
pause > nul