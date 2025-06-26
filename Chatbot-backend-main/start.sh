#!/bin/bash
cd /home/ec2-user/workmate/Chatbot-backend-main
source venv/bin/activate
exec uvicorn main:app --host 0.0.0.0 --port 8083 