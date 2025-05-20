@echo off
echo Starting Chatbot Application with Supabase...
echo.
echo Before running, make sure you have:
echo 1. Created a Supabase project (run setup_supabase.bat for instructions)
echo 2. Updated your .env file with your Supabase credentials
echo 3. Run setup_backend.bat and setup_frontend.bat
echo.
echo This will open two command windows:
echo 1. Backend server (http://localhost:8083)
echo 2. Frontend development server (http://localhost:3025)
echo.
echo Press any key to continue...
pause > nul

echo Starting backend server...
start cmd /k "run_backend.bat"

echo Starting frontend server...
start cmd /k "run_frontend.bat"

echo.
echo Both servers are starting. Please wait a moment...
echo Once both servers are running, you can access the application at:
echo http://localhost:3025
echo.