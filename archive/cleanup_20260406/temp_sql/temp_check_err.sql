SELECT id, status, left("executionData"::text, 2000) as data_preview FROM execution_entity WHERE "workflowId" = 'TgBossChat001' AND id = 174;
