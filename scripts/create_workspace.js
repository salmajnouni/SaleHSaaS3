// Create a workspace in AnythingLLM
// Run from: /app/server inside the container

const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function createWorkspace() {
  const name = 'SaleH';
  const slug = 'saleh';

  // Check if workspace already exists
  const existing = await p.workspaces.findFirst({ where: { slug: slug } });
  if (existing) {
    console.log('Workspace already exists: ' + existing.name + ' (slug: ' + existing.slug + ')');
    await p.$disconnect();
    return;
  }

  // Create workspace with Ollama settings
  const ws = await p.workspaces.create({
    data: {
      name: name,
      slug: slug,
      chatProvider: 'ollama',
      chatModel: 'llama3:latest',
      openAiTemp: 0.7,
      openAiHistory: 20,
      openAiPrompt: 'أنت مساعد ذكاء اصطناعي ذكي ومفيد. أجب دائماً باللغة العربية.',
      similarityThreshold: 0.25,
      topN: 4
    }
  });

  console.log('=== Workspace Created Successfully ===');
  console.log('Name: ' + ws.name);
  console.log('Slug: ' + ws.slug);
  console.log('ID: ' + ws.id);
  console.log('Chat Provider: ' + ws.chatProvider);
  console.log('Chat Model: ' + ws.chatModel);
  console.log('=====================================');
  console.log('Access at: http://localhost:3002/workspace/' + ws.slug);

  await p.$disconnect();
}

createWorkspace().catch(function(e) {
  console.error('Error:', e.message);
  process.exit(1);
});
