// Script to create admin user in AnythingLLM
// Run from: /app/server inside the container

const bcrypt = require('bcrypt');
const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = path.join('/app/server/storage', 'anythingllm.db');

async function createAdmin() {
  const username = 'saleh';
  const password = 'SaleHSaaS@2026!';
  const role = 'admin';

  // Hash the password
  const saltRounds = 10;
  const hashedPassword = await bcrypt.hash(password, saltRounds);

  const db = new Database(DB_PATH);

  // Check if user already exists
  const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
  if (existing) {
    console.log('User already exists: ' + username);
    db.close();
    return;
  }

  // Create admin user
  const stmt = db.prepare(
    'INSERT INTO users (username, password, role, suspended) VALUES (?, ?, ?, ?)'
  );
  const result = stmt.run(username, hashedPassword, role, 0);

  console.log('=== Admin Created Successfully ===');
  console.log('Username: ' + username);
  console.log('Password: ' + password);
  console.log('Role: ' + role);
  console.log('ID: ' + result.lastInsertRowid);
  console.log('==================================');
  console.log('Login at: http://localhost:3002');

  db.close();
}

createAdmin().catch(function(err) {
  console.error('Error:', err.message);
  process.exit(1);
});
