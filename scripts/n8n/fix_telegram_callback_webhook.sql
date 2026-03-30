BEGIN;

UPDATE workflow_entity
SET
  nodes = replace(
            replace(nodes::text, '📩 Telegram Callback Trigger', 'Telegram Callback Trigger'),
            '≡اôر Telegram Callback Trigger',
            'Telegram Callback Trigger'
          )::json,
  connections = replace(
                  replace(connections::text, '📩 Telegram Callback Trigger', 'Telegram Callback Trigger'),
                  '≡اôر Telegram Callback Trigger',
                  'Telegram Callback Trigger'
                )::json
WHERE id = 'CwCounclTele001';

UPDATE webhook_entity
SET
  "node" = 'Telegram Callback Trigger',
  "webhookPath" = 'CwCounclTele001/telegram-callback-trigger/webhook'
WHERE "workflowId" = 'CwCounclTele001';

COMMIT;
