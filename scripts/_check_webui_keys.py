import sqlite3

ALLOWED_TABLES = {
    "user",
    "api_key",
    "auth",
    "chat",
    "chatid",
    "function",
    "model",
    "config",
    "tool",
    "memory",
    "document",
}

db = sqlite3.connect("/app/backend/data/webui.db")
cur = db.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall() if r[0] in ALLOWED_TABLES]
print("Tables:", tables)

cur.execute("SELECT id, email, role FROM user LIMIT 5")
for row in cur.fetchall():
    print(f"User: id={row[0]} email={row[1]} role={row[2]}")

for t in tables:
    cur.execute("PRAGMA table_info(?)", (t,))
    cols = [r[1] for r in cur.fetchall()]
    key_cols = [c for c in cols if "key" in c.lower() or "token" in c.lower() or "secret" in c.lower()]
    if key_cols:
        print(f"\nTable '{t}' has key-related cols: {key_cols}")
        cur.execute(f"SELECT * FROM {t} LIMIT 3")
        for r in cur.fetchall():
            print(f"  {r}")

db.close()