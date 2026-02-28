// Check AnythingLLM workspace and system settings
const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function check() {
  console.log('=== Workspaces ===');
  const ws = await p.workspaces.findMany();
  console.log(JSON.stringify(ws, null, 2));

  console.log('\n=== System Settings ===');
  const settings = await p.system_settings.findMany();
  console.log(JSON.stringify(settings, null, 2));

  console.log('\n=== Users ===');
  const users = await p.users.findMany({
    select: { id: true, username: true, role: true, suspended: true }
  });
  console.log(JSON.stringify(users, null, 2));

  await p.$disconnect();
}

check().catch(function(e) {
  console.error('Error:', e.message);
  process.exit(1);
});
