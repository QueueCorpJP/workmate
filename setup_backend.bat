@echo off
cd Chatbot-backend-main
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
pip install supabase
playwright install
echo Creating .env file with Supabase configuration...
(
echo GOOGLE_API_KEY=dummy_key
echo COMPANY_NAME="Queue"
echo # Supabase configuration
echo SUPABASE_URL=https://your-supabase-project-url.supabase.co
echo SUPABASE_KEY=your-supabase-anon-key
echo # Database connection (will use Supabase PostgreSQL)
echo DB_NAME=postgres
echo DB_USER=postgres
echo DB_PASSWORD=postgres
echo DB_HOST=db.your-supabase-project-url.supabase.co
echo DB_PORT=5432
) > .env
echo Backend setup complete!