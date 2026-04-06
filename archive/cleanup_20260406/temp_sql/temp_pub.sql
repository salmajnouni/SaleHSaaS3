-- Publish and activate the new version
UPDATE workflow_entity 
SET "activeVersionId" = "versionId", active = true
WHERE id = 'CwCounclWbhk001';

-- Verify
SELECT id, active, "versionId" = "activeVersionId" as published
FROM workflow_entity WHERE id = 'CwCounclWbhk001';
