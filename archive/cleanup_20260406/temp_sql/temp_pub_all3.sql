-- Publish TgBossChat001, CwCounclTele001, CwCounclWbhk001
UPDATE workflow_entity SET "activeVersionId" = "versionId", active = true WHERE id = 'TgBossChat001';
UPDATE workflow_entity SET "activeVersionId" = "versionId", active = true WHERE id = 'CwCounclTele001';
UPDATE workflow_entity SET "activeVersionId" = "versionId", active = true WHERE id = 'CwCounclWbhk001';
