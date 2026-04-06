-- Check execution_data columns
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'execution_data' ORDER BY ordinal_position;
-- Check if there's data
SELECT "executionId", length(data) as data_len, length("workflowData"::text) as wf_len FROM execution_data WHERE "executionId" = '164';
