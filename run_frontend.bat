@echo off
echo Setting up frontend with local API URL...
cd Chatbot-Frontend-main
echo VITE_API_URL=http://localhost:8083/chatbot/api > .env
npm run dev --host