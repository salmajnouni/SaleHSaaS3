-- Get the latest execution error details
SELECT id, status, "stoppedAt",
  substring(data::text from '"error":\s*\{[^}]*"message":"([^"]*)"') as error_msg,
  substring(data::text from '"lastNodeExecuted":"([^"]*)"') as last_node
FROM execution_entity 
WHERE "workflowId" = 'CwCounclWbhk001'
ORDER BY "createdAt" DESC LIMIT 3;
