-- Set activeVersionId to match versionId (publish the workflow)
UPDATE workflow_entity 
SET "activeVersionId" = "versionId"
WHERE id = 'CwCounclWbhk001';

-- Verify
SELECT id, active, "versionId" as draft_vid, "activeVersionId" as active_vid
FROM workflow_entity WHERE id = 'CwCounclWbhk001';
