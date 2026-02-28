const { PrismaClient } = require('./node_modules/@prisma/client');
const bcrypt = require('./node_modules/bcrypt');

const db = new PrismaClient();

async function createAdmin() {
  const username = 'saleh';
  const password = 'SaleHSaaS@2026!';
  const role = 'admin';

  // Hash the password
  const saltRounds = 10;
  const hashedPassword = await bcrypt.hash(password, saltRounds);

  // Check if user already exists
  const existing = await db.users.findFirst({ where: { username: username } });
  if (existing) {
    console.log('User already exists: ' + username);
    await db.$disconnect();
    return;
  }

  // Create admin user
  const user = await db.users.create({
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

  await db.$disconnect();
}

createAdmin().catch(function(err) {
  console.error('Error:', err.message);
  process.exit(1);
});
