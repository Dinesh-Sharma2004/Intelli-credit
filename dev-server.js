#!/usr/bin/env node

/**
 * Intelli-Credit Development Server
 * Starts both frontend and backend servers for local development
 */

const { spawn } = require('child_process');
const path = require('path');

const backendDir = path.join(__dirname, 'backend');
const frontendDir = path.join(__dirname, 'frontend');

console.log('🚀 Starting Intelli-Credit Development Servers\n');

// Start Backend
console.log('Starting Backend API on http://localhost:8000...');
const backendProcess = spawn('uvicorn', ['main:app', '--reload', '--port', '8000'], {
  cwd: backendDir,
  stdio: 'inherit',
  shell: true
});

// Start Frontend
console.log('Starting Frontend on http://localhost:3000...');
const frontendProcess = spawn('npm', ['run', 'dev'], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: true
});

// Handle cleanup
process.on('SIGINT', () => {
  console.log('\n\n🛑 Shutting down development servers...');
  backendProcess.kill();
  frontendProcess.kill();
  process.exit();
});

// Handle errors
backendProcess.on('error', (error) => {
  console.error('Backend error:', error);
});

frontendProcess.on('error', (error) => {
  console.error('Frontend error:', error);
});
