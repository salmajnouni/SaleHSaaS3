BEGIN;

DELETE FROM webhook_entity
WHERE "workflowId" = 'CwCounclTele001'
  AND "webhookPath" = 'CwCounclTele001/%F0%9F%93%A9%20telegram%20callback%20trigger/webhook';

COMMIT;
