UPDATE workflow_entity SET "activeVersionId" = "versionId", active = true WHERE id = 'CwCounclTele001';
UPDATE workflow_entity SET "activeVersionId" = "versionId", active = true WHERE id = 'CwCounclWbhk001';
SELECT id, active, published FROM workflow_entity WHERE id IN ('CwCounclTele001', 'CwCounclWbhk001');
