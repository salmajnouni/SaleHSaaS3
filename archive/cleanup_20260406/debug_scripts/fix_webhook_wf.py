"""Fix the advisory council webhook workflow in n8n database."""
import json
import subprocess

# Read the corrected workflow JSON file
with open(r"n8n\workflows\advisory_council_webhook.json", "r", encoding="utf-8") as f:
    wf = json.load(f)

nodes_json = json.dumps(wf["nodes"], ensure_ascii=False)
connections_json = json.dumps(wf["connections"], ensure_ascii=False)
settings_json = json.dumps(wf.get("settings", {}), ensure_ascii=False)

# Escape single quotes for SQL
nodes_sql = nodes_json.replace("'", "''")
connections_sql = connections_json.replace("'", "''")
settings_sql = settings_json.replace("'", "''")

sql = f"""
-- Update the main workflow entity
UPDATE workflow_entity 
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json,
    settings = '{settings_sql}'::json,
    active = true
WHERE id = 'CwCounclWbhk001';

-- Also update the workflow_history version that n8n actually executes
UPDATE workflow_history
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json
WHERE "workflowId" = 'CwCounclWbhk001';
"""

# Write SQL to temp file
with open("temp_fix.sql", "w", encoding="utf-8") as f:
    f.write(sql)

# Copy and execute
subprocess.run(["docker", "cp", "temp_fix.sql", "salehsaas_postgres:/tmp/fix.sql"], check=True)
result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas", "-f", "/tmp/fix.sql"],
    capture_output=True, text=True
)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
print("return code:", result.returncode)
