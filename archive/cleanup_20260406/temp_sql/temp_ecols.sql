-- List columns of execution_entity
SELECT column_name FROM information_schema.columns WHERE table_name='execution_entity' ORDER BY ordinal_position;
