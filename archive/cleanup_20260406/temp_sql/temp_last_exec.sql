SELECT id, "workflowId", finished, "stoppedAt", status
FROM execution_entity
WHERE "workflowId" = 'CwCounclWbhk001'
ORDER BY "createdAt" DESC
LIMIT 3;
