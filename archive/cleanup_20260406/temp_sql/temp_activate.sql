-- Check history entries
SELECT count(*) as history_count FROM workflow_history WHERE "workflowId"='CwCounclWbhk001';

-- Get latest version
SELECT "versionId" FROM workflow_history WHERE "workflowId"='CwCounclWbhk001' ORDER BY "createdAt" DESC LIMIT 1;

-- Check workflow state
SELECT active, "versionId" as vid FROM workflow_entity WHERE id='CwCounclWbhk001';
