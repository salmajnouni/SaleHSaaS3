// Fix AnythingLLM Vector DB - Switch from QDrant to LanceDB (built-in, no auth needed)
// Run from: /app/server inside the container

const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function fixVectorDB() {
  console.log('=== Fixing Vector DB Configuration ===');

  // Check current VectorDB setting
  const current = await p.system_settings.findFirst({
    where: { label: 'VectorDB' }
  });

  if (current) {
    console.log('Current VectorDB: ' + current.value);
    // Update to lancedb
    await p.system_settings.update({
      where: { id: current.id },
      data: { value: 'lancedb' }
    });
    console.log('Updated VectorDB to: lancedb');
  } else {
    // Create the setting
    await p.system_settings.create({
      data: {
        label: 'VectorDB',
        value: 'lancedb'
      }
    });
    console.log('Created VectorDB setting: lancedb');
  }

  // Remove any QDrant-specific settings
  const qdrantSettings = await p.system_settings.findMany({
    where: {
      label: {
        startsWith: 'QdrantDB'
      }
    }
  });

  if (qdrantSettings.length > 0) {
    for (const s of qdrantSettings) {
      await p.system_settings.delete({ where: { id: s.id } });
      console.log('Removed QDrant setting: ' + s.label);
    }
  }

  // Verify final settings
  console.log('\n=== Final Vector DB Settings ===');
  const vectorSettings = await p.system_settings.findMany({
    where: {
      OR: [
        { label: 'VectorDB' },
        { label: { startsWith: 'Lance' } },
        { label: { startsWith: 'Qdrant' } }
      ]
    }
  });
  console.log(JSON.stringify(vectorSettings, null, 2));

  console.log('\n✅ Done! Restart AnythingLLM container for changes to take effect.');
  await p.$disconnect();
}

fixVectorDB().catch(function(e) {
  console.error('Error:', e.message);
  process.exit(1);
});
