-- Compare workflow properties between working and broken workflows
SELECT id, active, "versionId" as vid 
FROM workflow_entity 
WHERE id IN ('CwCounclTele001', 'CwCounclWbhk001', 'HuuRe6ooTrbh5rJF');

-- Check if there's a published_version or similar 
SELECT column_name FROM information_schema.columns WHERE table_name='workflow_entity' ORDER BY ordinal_position;

-- Check workflow_history for working vs broken
SELECT "workflowId", "versionId", "autosaved", "createdAt"
FROM workflow_history 
WHERE "workflowId" IN ('CwCounclTele001', 'CwCounclWbhk001')
ORDER BY "createdAt" DESC LIMIT 5;
