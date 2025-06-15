module.exports = {
  apps: [{
    name: 'chatbot-backend',
    script: './venv/bin/uvicorn',
    args: 'main:app --host 0.0.0.0 --port 8083',
    cwd: '/home/ec2-user/workmate/Chatbot-backend-main',
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: '8083'
    },
    error_file: '/home/ec2-user/.pm2/logs/chatbot-backend-error.log',
    out_file: '/home/ec2-user/.pm2/logs/chatbot-backend-out.log',
    log_file: '/home/ec2-user/.pm2/logs/chatbot-backend-combined.log',
    time: true
  }]
}; 