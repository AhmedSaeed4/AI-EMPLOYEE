/**
 * PM2 Ecosystem Configuration for Cloud Deployment
 *
 * This file configures PM2 to run on Oracle Cloud Free Tier.
 *
 * Apps:
 *   1. ai-employee-api    - Deduplication API server (port 5000)
 *   2. ai-employee-cloud  - Cloud orchestrator with watchers
 *
 * Usage:
 *   pm2 start ecosystem.cloud.config.js
 *   pm2 save
 *   pm2 startup
 *
 * Commands:
 *   pm2 status              - Check status
 *   pm2 logs                - View all logs
 *   pm2 logs ai-employee-api - View API logs
 *   pm2 restart all         - Restart all
 *   pm2 stop all            - Stop all
 */

module.exports = {
  apps: [
    // ========== DEDUPLICATION API ==========
    {
      name: 'ai-employee-api',

      // Script to run
      script: 'cloud/api_server.py',

      // Use UV virtual environment Python
      interpreter: '/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/ai_employee_scripts/.venv/bin/python',

      // Working directory
      cwd: '/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/ai_employee_scripts',

      // Environment variables
      env: {
        NODE_ENV: 'production',
        DEDUP_API_PORT: 5000,
        // DEDUP_API_KEY: 'your-secret-key',  // Set in .env or here
      },

      // Auto-restart configuration
      watch: false,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',

      // Logging
      error_file: './logs/api-err.log',
      out_file: './logs/api-out.log',
      log_file: './logs/api-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      // Process management
      instances: 1,
      exec_mode: 'fork',

      // Memory and CPU limits
      max_memory_restart: '256M',
      kill_timeout: 5000,
    },

    // ========== CLOUD ORCHESTRATOR ==========
    {
      name: 'ai-employee-cloud',

      // Script to run
      script: 'cloud/cloud_orchestrator.py',

      // Use UV virtual environment Python
      interpreter: '/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/ai_employee_scripts/.venv/bin/python',

      // Working directory
      cwd: '/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/ai_employee_scripts',

      // Environment variables
      env: {
        NODE_ENV: 'production',
        DEDUP_API_URL: 'http://localhost:5000',  // Connect to local API
      },

      // Auto-restart configuration
      watch: false,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',

      // Logging
      error_file: './logs/cloud-err.log',
      out_file: './logs/cloud-out.log',
      log_file: './logs/cloud-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      // Process management
      instances: 1,
      exec_mode: 'fork',

      // Memory and CPU limits
      max_memory_restart: '1G',
      kill_timeout: 5000,
      wait_ready: true,
    }
  ]
};
