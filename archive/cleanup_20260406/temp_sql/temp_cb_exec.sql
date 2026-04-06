SELECT id, status, finished, "stoppedAt"
FROM execution_entity
WHERE "workflowId" = 'CwCounclTele001'
ORDER BY "createdAt" DESC
LIMIT 5;
