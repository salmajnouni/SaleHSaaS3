const { PrismaClient } = require('./node_modules/@prisma/client');
const db = new PrismaClient();
const settings = [
  ['LLMProvider', 'ollama'],
  ['OllamaLLMBasePath', 'http://ollama:11434'],
  ['OllamaLLMModelPref', 'llama3:latest'],
  ['EmbeddingEngine', 'ollama'],
  ['EmbeddingBasePath', 'http://ollama:11434'],
  ['EmbeddingModelPref', 'qwen3-embedding:0.6b']
];
async function fix() {
  for (const [label, value] of settings) {
    await db.system_settings.upsert({
      where: { label: label },
      update: { value: value },
      create: { label: label, value: value }
    });
    console.log('Set: ' + label + ' = ' + value);
  }
  await db.$disconnect();
  console.log('All done!');
}
fix().catch(console.error);
