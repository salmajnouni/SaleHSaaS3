const { PrismaClient } = require('./node_modules/@prisma/client');
const db = new PrismaClient();
db.system_settings.findMany().then(function(rows) {
  console.log('=== AnythingLLM Settings ===');
  rows.forEach(function(s) {
    console.log(s.label + ' = ' + s.value);
  });
  return db.$disconnect();
}).catch(console.error);
