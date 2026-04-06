SELECT substring(data, position('jsonBody' in data), 500) FROM execution_data WHERE "executionId" = 152;
