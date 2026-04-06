-- Check activeVersionId for all workflows
SELECT id, active, "versionId" as draft_vid, "activeVersionId" as active_vid
FROM workflow_entity 
WHERE id IN ('CwCounclTele001', 'CwCounclWbhk001', 'HuuRe6ooTrbh5rJF');
