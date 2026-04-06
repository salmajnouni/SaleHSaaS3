-- Get execution error from execution_data for latest execution 158
SELECT 
  substring("data"::text from '"lastNodeExecuted":"([^"]*)"') as last_node,
  substring("data"::text from '"errorMessage":"([^"]*)"') as error_message,
  substring("data"::text from 1 for 1) as first_char,
  length("data"::text) as data_len
FROM execution_data
WHERE "executionId" = 158;
