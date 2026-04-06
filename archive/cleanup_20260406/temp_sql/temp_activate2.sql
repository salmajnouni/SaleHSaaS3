-- Activate the workflow
UPDATE workflow_entity SET active = true WHERE id='CwCounclWbhk001';

-- Verify
SELECT id, active FROM workflow_entity WHERE id='CwCounclWbhk001';
