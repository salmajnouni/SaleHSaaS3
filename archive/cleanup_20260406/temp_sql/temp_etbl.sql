-- Check execution data table
SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%execution%';

-- Get recent executions
SELECT id, status, "stoppedAt"::text
FROM execution_entity 
WHERE "workflowId" = 'CwCounclWbhk001'
ORDER BY "createdAt" DESC LIMIT 3;
