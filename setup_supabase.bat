@echo off
echo ===================================================
echo Supabase Setup Guide for Chatbot Application
echo ===================================================
echo.
echo This guide will help you set up a Supabase project for the chatbot application.
echo.
echo Steps:
echo 1. Go to https://supabase.com and sign up or log in
echo 2. Create a new project
echo 3. Choose a name for your project
echo 4. Set a secure database password (save it for later)
echo 5. Choose a region close to you
echo 6. Wait for your database to be ready
echo.
echo Once your project is created:
echo 1. Go to Project Settings -^> API
echo 2. Copy the "Project URL" and "anon public" key
echo 3. Open the .env file in the Chatbot-backend-main directory
echo 4. Replace the placeholder values with your actual Supabase details:
echo    - SUPABASE_URL: Your project URL
echo    - SUPABASE_KEY: Your anon key
echo    - DB_HOST: The database host (db.[your-project-reference].supabase.co)
echo    - DB_PASSWORD: The database password you set when creating the project
echo.
echo After updating the .env file, run setup_backend.bat again to apply the changes.
echo.
echo Press any key to open the Supabase website...
pause > nul
start https://supabase.com
echo.
echo Press any key to exit...
pause > nul