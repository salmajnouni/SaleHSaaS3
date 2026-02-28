const { PrismaClient } = require('./node_modules/@prisma/client');
const db = new PrismaClient();
async function check() {
  const users = await db.users.findMany({
    select: { username: true, role: true, suspended: true }
  });
  console.log('=== Users ===');
  console.log(JSON.stringify(users, null, 2));
  
  const authToken = await db.system_settings.findFirst({
    where: { label: 'multi_user_mode' }
  });
  console.log('=== Multi User Mode ===');
  console.log(authToken ? authToken.value : 'not set');
  
  await db.$disconnect();
}
check().catch(console.error);
