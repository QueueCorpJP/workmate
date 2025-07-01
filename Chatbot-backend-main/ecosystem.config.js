module.exports = {
  apps: [{
    name: 'chatbot-backend',
    script: 'main.py',
    interpreter: '/home/ec2-user/workmate/Chatbot-backend-main/venv/bin/python',
    cwd: '/home/ec2-user/workmate/Chatbot-backend-main',
    env: {
      NODE_ENV: 'production',
      PORT: 8083,
      ENVIRONMENT: 'production'
    },
    max_restarts: 5,
    min_uptime: '10s',
    restart_delay: 4000,
    error_file: '/home/ec2-user/.pm2/logs/chatbot-backend-error.log',
    out_file: '/home/ec2-user/.pm2/logs/chatbot-backend-out.log',
    log_file: '/home/ec2-user/.pm2/logs/chatbot-backend.log',
    time: true
  }]
}; 