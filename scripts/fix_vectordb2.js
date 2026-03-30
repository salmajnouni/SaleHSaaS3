// Fix AnythingLLM Vector DB - Complete fix including all QDrant settings
// Run from: /app/server inside the container
// Legacy-only helper: this script is not part of current default runtime.
// Set ALLOW_LEGACY_ANYTHINGLLM_FIX=true to run intentionally.

const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function fixVectorDB() {
  if (process.env.ALLOW_LEGACY_ANYTHINGLLM_FIX !== 'true') {
    console.log('Skipped: legacy AnythingLLM fix is disabled by default.');
    console.log('Set ALLOW_LEGACY_ANYTHINGLLM_FIX=true if you really want to run it.');
    return;
  }

  console.log('=== Complete Vector DB Fix ===\n');

  // Show all current settings
  const allSettings = await p.system_settings.findMany();
  console.log('Current settings count:', allSettings.length);

  // Find and remove ALL QDrant-related settings
  const qdrantLabels = [
    'VectorDB', 'QdrantDBEndpoint', 'QdrantDBApiKey',
    'QdrantCloudEndpoint', 'QdrantApiKey', 'QdrantEndpoint'
  ];

  for (const label of qdrantLabels) {
    const setting = await p.system_settings.findFirst({ where: { label: label } });
    if (setting) {
      console.log('Found: ' + label + ' = ' + setting.value);
      if (label === 'VectorDB') {
        // Update VectorDB to lancedb
        await p.system_settings.update({
          where: { id: setting.id },
          data: { value: 'lancedb' }
        });
        console.log('  -> Updated to: lancedb');
      } else {
        // Remove QDrant-specific settings
        await p.system_settings.delete({ where: { id: setting.id } });
        console.log('  -> Deleted');
      }
    }
  }

  // Also search for any setting containing 'qdrant' case-insensitive
  const allAfter = await p.system_settings.findMany();
  for (const s of allAfter) {
    if (s.label.toLowerCase().includes('qdrant') || 
        (s.value && s.value.toLowerCase().includes('qdrant'))) {
      console.log('Found QDrant reference: ' + s.label + ' = ' + s.value);
      await p.system_settings.delete({ where: { id: s.id } });
      console.log('  -> Deleted');
    }
  }

  // Ensure VectorDB=lancedb exists
  const vectorDB = await p.system_settings.findFirst({ where: { label: 'VectorDB' } });
  if (!vectorDB) {
    await p.system_settings.create({
      data: { label: 'VectorDB', value: 'lancedb' }
    });
    console.log('Created VectorDB = lancedb');
  }

  // Final verification
  console.log('\n=== Final Settings ===');
  const finalSettings = await p.system_settings.findMany();
  for (const s of finalSettings) {
    console.log(s.label + ' = ' + s.value);
  }

  console.log('\n✅ Done! Restart the container now.');
  await p.$disconnect();
}

fixVectorDB().catch(function(e) {
  console.error('Error:', e.message);
  process.exit(1);
});
