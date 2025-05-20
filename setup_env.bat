@echo off
REM 環境変数の設定
SET GOOGLE_API_KEY=your_google_api_key_here
SET COMPANY_NAME=Workmate
SET DB_NAME=chatbot
SET DB_USER=postgres
SET DB_PASSWORD=password
SET DB_HOST=localhost
SET DB_PORT=5432

echo 環境変数が設定されました。
echo Google API Keyを適切な値に変更してください。
echo.
echo 現在の設定:
echo GOOGLE_API_KEY=%GOOGLE_API_KEY%
echo COMPANY_NAME=%COMPANY_NAME%
echo DB_NAME=%DB_NAME%
echo DB_USER=%DB_USER%
echo DB_PASSWORD=%DB_PASSWORD%
echo DB_HOST=%DB_HOST%
echo DB_PORT=%DB_PORT% 