INSERT INTO variables (key, value, type)
VALUES ('TELEGRAM_BOT_TOKEN', '8631392889:AAF4jdcNrWWHsvXY_Y2pnY5C-7eJa0678Fg', 'string')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
SELECT key, value FROM variables WHERE key = 'TELEGRAM_BOT_TOKEN';
