module.exports = {
  apps: [{
    name: 'chatbot-backend',
    script: './start.sh',
    cwd: '/home/ec2-user/workmate/Chatbot-backend-main',
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      ENVIRONMENT: 'production',
      PORT: '8083'
    },
    error_file: '/home/ec2-user/.pm2/logs/chatbot-backend-error.log',
    out_file: '/home/ec2-user/.pm2/logs/chatbot-backend-out.log',
    log_file: '/home/ec2-user/.pm2/logs/chatbot-backend-combined.log',
    time: true
  }]
}; 