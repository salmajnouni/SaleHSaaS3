// Script to create admin user in AnythingLLM
// Run from: /app/server inside the container
// Uses bcryptjs (pure JS, no native bindings needed)

const bcrypt = require('bcryptjs');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function createAdmin() {
  const username = 'saleh';
  const password = 'SaleHSaaS@2026!';
  const role = 'admin';

  // Hash the password with bcryptjs
  const saltRounds = 10;
  const hashedPassword = await bcrypt.hash(password, saltRounds);

  // Check if user already exists
  const existing = await prisma.users.findFirst({ where: { username: username } });
  if (existing) {
    console.log('User already exists: ' + username);
    console.log('Role: ' + existing.role);
    await prisma.$disconnect();
    return;
  }

  // Create admin user
  const user = await prisma.users.create({
    data: {
      username: username,
      password: hashedPassword,
      role: role,
      suspended: 0
    }
  });

  console.log('=== Admin Created Successfully ===');
  console.log('Username: ' + username);
  console.log('Password: ' + password);
  console.log('Role: ' + role);
  console.log('ID: ' + user.id);
  console.log('==================================');
  console.log('Login at: http://localhost:3002');

  await prisma.$disconnect();
}

createAdmin().catch(function(err) {
  console.error('Error:', err.message);
  process.exit(1);
});
