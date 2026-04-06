-- Extract the error from the compressed data
-- Try a broader search pattern
SELECT 
  -- Check data format
  substring("data"::text from 1 for 20) as data_start,
  -- Try extracting error-related text
  position('error' in lower("data"::text)) as error_pos,
  position('invalid' in lower("data"::text)) as invalid_pos,
  position('syntax' in lower("data"::text)) as syntax_pos,
  CASE WHEN position('error' in lower("data"::text)) > 0 
    THEN substring("data"::text from greatest(position('error' in lower("data"::text)) - 10, 1) for 200) 
    ELSE NULL END as error_context
FROM execution_data
WHERE "executionId" = 158;
