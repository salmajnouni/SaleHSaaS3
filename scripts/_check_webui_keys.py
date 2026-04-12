import sqlite3, json

db = sqlite3.connect("/app/backend/data/webui.db")
cur = db.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

# Find user info
cur.execute("SELECT id, email, role FROM user LIMIT 5")
for row in cur.fetchall():
    print(f"User: id={row[0]} email={row[1]} role={row[2]}")

# Check for API key related tables
for t in tables:
    cur.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in cur.fetchall()]
    key_cols = [c for c in cols if "key" in c.lower() or "token" in c.lower() or "secret" in c.lower()]
    if key_cols:
        print(f"\nTable '{t}' has key-related cols: {key_cols}")
        cur.execute(f"SELECT * FROM {t} LIMIT 3")
        for r in cur.fetchall():
            print(f"  {r}")

db.close()
