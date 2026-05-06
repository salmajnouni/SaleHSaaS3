"""
جامع لوقات Docker → PostgreSQL
يشتغل في الخلفية كل 60 ثانية، يجمع لوقات جميع الكونتينرات ويخزنها في جدول service_logs.
يحلل مستوى اللوق (ERROR/WARNING/INFO) ويحفظ الرسائل المهمة فقط.
"""

import subprocess
import re
import time
import sys
import os
import logging
from datetime import datetime, timezone

# Add parent dir to path for .env loading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("log_collector")

# ── Config ──────────────────────────────────────────────
CONTAINERS = [
    "salehsaas_webui",
    "salehsaas_n8n",
    "salehsaas_searxng",
    "salehsaas_chromadb",
    "salehsaas_pipelines",
    "salehsaas_tika",
    "salehsaas_data_pipeline",
    "salehsaas_postgres",
    "salehsaas_watcher",
    "salehsaas_task_runners",
]

COLLECT_INTERVAL = 60  # seconds
LOG_SINCE = "65s"  # overlap slightly to avoid missing lines

# Log level patterns
ERROR_PATTERNS = re.compile(
    r"\b(ERROR|CRITICAL|FATAL|Exception|Traceback|raise |"
    r"HTTPStatusError|ConnectionRefused|TimeoutError|"
    r"ECONNREFUSED|ENOTFOUND|failed|panic|OOM|killed)\b",
    re.IGNORECASE,
)
WARN_PATTERNS = re.compile(
    r"\b(WARN|WARNING|deprecated|retry|retrying|slow|"
    r"timeout|429|503|502|rate.limit)\b",
    re.IGNORECASE,
)

# Lines to skip (noisy / not useful)
SKIP_PATTERNS = re.compile(
    r"(GET /api/v1/chats|GET /app/version|GET /health|"
    r"OPTIONS /|HEAD /|favicon\.ico|"
    r"INFO\s+\|\s+uvicorn\.protocols|"
    r"get_all_models|static/|\.js\s|\.css\s|\.woff)",
    re.IGNORECASE,
)

# Timestamp patterns in Docker logs
DOCKER_TS = re.compile(r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z?)\s*\|?\s*")


def get_db_conn():
    """Connect to PostgreSQL (via Docker network IP since no port mapping)."""
    import psycopg2
    env = {}
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v

    # Try localhost first (if port mapped), fallback to Docker IP
    hosts = ["localhost", "172.20.0.10"]
    last_err = None
    for host in hosts:
        try:
            conn = psycopg2.connect(
                host=host,
                port=5432,
                dbname="salehsaas",
                user="salehsaas",
                password=env.get("POSTGRES_PASSWORD", ""),
                connect_timeout=5,
            )
            return conn
        except Exception as e:
            last_err = e
    raise last_err


def classify_level(line: str) -> str:
    """Classify log line as ERROR, WARNING, or INFO."""
    if ERROR_PATTERNS.search(line):
        return "ERROR"
    if WARN_PATTERNS.search(line):
        return "WARNING"
    return "INFO"


def parse_timestamp(line: str):
    """Try to extract timestamp from log line."""
    m = DOCKER_TS.match(line)
    if m:
        ts_str = m.group(1).rstrip("Z")
        try:
            return datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def collect_logs(container: str) -> list:
    """Get recent Docker logs for a container."""
    try:
        result = subprocess.run(
            ["docker", "logs", "--since", LOG_SINCE, "--timestamps", container],
            capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace",
        )
        output = result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    entries = []
    for raw_line in output.splitlines():
        raw_line = raw_line.strip()
        if not raw_line or len(raw_line) < 10:
            continue

        # Skip noisy lines
        if SKIP_PATTERNS.search(raw_line):
            continue

        level = classify_level(raw_line)

        # Only store ERROR and WARNING (skip INFO to save space)
        if level == "INFO":
            continue

        ts = parse_timestamp(raw_line)

        # Clean message: remove timestamp prefix
        msg = DOCKER_TS.sub("", raw_line).strip()
        # Remove redundant level prefix
        msg = re.sub(r"^(ERROR|WARNING|WARN|INFO|DEBUG)\s*[\|:]\s*", "", msg, flags=re.IGNORECASE).strip()

        if len(msg) < 5:
            continue

        entries.append({
            "container": container.replace("salehsaas_", ""),
            "level": level,
            "message": msg[:2000],  # cap at 2000 chars
            "raw_line": raw_line[:4000],
            "log_timestamp": ts,
        })

    return entries


def store_logs(conn, entries: list):
    """Insert log entries into PostgreSQL, deduplicating by message hash."""
    if not entries:
        return 0

    cur = conn.cursor()
    inserted = 0
    for e in entries:
        # Deduplicate: skip if same container+message exists in last 5 minutes
        cur.execute(
            """SELECT 1 FROM service_logs
               WHERE container = %s AND message = %s
               AND collected_at > NOW() - INTERVAL '5 minutes'
               LIMIT 1""",
            (e["container"], e["message"]),
        )
        if cur.fetchone():
            continue

        cur.execute(
            """INSERT INTO service_logs (container, level, message, raw_line, log_timestamp)
               VALUES (%s, %s, %s, %s, %s)""",
            (e["container"], e["level"], e["message"], e["raw_line"], e["log_timestamp"]),
        )
        inserted += 1

    conn.commit()
    cur.close()
    return inserted


def cleanup_old_logs(conn, days: int = 7):
    """Delete logs older than N days."""
    cur = conn.cursor()
    cur.execute("DELETE FROM service_logs WHERE collected_at < NOW() - INTERVAL '%s days'", (days,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    return deleted


def run_once(conn):
    """Single collection cycle."""
    total_entries = 0
    total_inserted = 0
    for container in CONTAINERS:
        entries = collect_logs(container)
        if entries:
            inserted = store_logs(conn, entries)
            total_entries += len(entries)
            total_inserted += inserted
            if inserted > 0:
                log.info(f"  {container}: {inserted} new ({len(entries)} found)")
    return total_entries, total_inserted


def main():
    log.info("🔍 Log Collector starting...")
    log.info(f"   Containers: {len(CONTAINERS)}")
    log.info(f"   Interval: {COLLECT_INTERVAL}s")
    log.info(f"   Only storing: ERROR + WARNING")

    conn = get_db_conn()
    log.info("✅ Connected to PostgreSQL")

    cycle = 0
    while True:
        try:
            cycle += 1
            found, inserted = run_once(conn)

            if inserted > 0:
                log.info(f"Cycle {cycle}: {inserted} new logs stored (from {found} found)")

            # Cleanup old logs every 100 cycles (~every ~1.5 hours)
            if cycle % 100 == 0:
                deleted = cleanup_old_logs(conn)
                if deleted:
                    log.info(f"Cleanup: removed {deleted} old logs")

        except Exception as e:
            log.error(f"Cycle {cycle} error: {e}")
            try:
                conn.close()
            except Exception:
                pass
            try:
                conn = get_db_conn()
                log.info("Reconnected to PostgreSQL")
            except Exception as e2:
                log.error(f"Reconnect failed: {e2}")

        time.sleep(COLLECT_INTERVAL)


if __name__ == "__main__":
    main()
