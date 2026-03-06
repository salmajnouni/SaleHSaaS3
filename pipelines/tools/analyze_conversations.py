#!/usr/bin/env python3
"""
analyze_conversations.py — SaleHSaaS v2.1.0
تحليل بيانات المحادثات من PostgreSQL وطباعة تقرير منسّق

الاستخدام:
    python analyze_conversations.py [--days 30] [--domain all]

المتطلبات:
    pip install psycopg2-binary tabulate
"""

import os
import sys
import argparse
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# ── إعداد الاتصال ─────────────────────────────────────────────────────────────

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST",     "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname":   os.getenv("POSTGRES_DB",       "salehsaas"),
    "user":     os.getenv("POSTGRES_USER",     "salehsaas"),
    "password": os.getenv("POSTGRES_PASSWORD", "salehsaas_pass"),
}


def connect():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"ERROR: Cannot connect to PostgreSQL: {e}")
        print(f"Config: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
        sys.exit(1)


def query(conn, sql, params=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def print_table(rows, title=""):
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    if not rows:
        print("  (لا توجد بيانات)")
        return
    if HAS_TABULATE:
        print(tabulate(rows, headers="keys", tablefmt="rounded_outline", floatfmt=".2f"))
    else:
        # طباعة بسيطة بدون tabulate
        if rows:
            headers = list(rows[0].keys())
            print("  " + " | ".join(str(h).ljust(15) for h in headers))
            print("  " + "-" * (17 * len(headers)))
            for row in rows:
                print("  " + " | ".join(str(v)[:14].ljust(15) for v in row.values()))


# ── الاستعلامات ───────────────────────────────────────────────────────────────

def summary(conn, days):
    return query(conn, """
        SELECT
            COUNT(*)                                           AS total,
            COUNT(DISTINCT session_id)                         AS sessions,
            ROUND(AVG(response_time_ms) / 1000.0, 2)          AS avg_sec,
            ROUND(AVG(tokens_used))                            AS avg_tokens,
            SUM(CASE WHEN rag_used THEN 1 ELSE 0 END)          AS rag_count,
            ROUND(100.0 * SUM(CASE WHEN rag_used THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS rag_pct
        FROM conversation_logs
        WHERE timestamp >= NOW() - INTERVAL '%s days'
    """, (days,))


def by_domain(conn, days):
    return query(conn, """
        SELECT
            expert_domain                                      AS domain,
            COUNT(*)                                           AS count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct,
            ROUND(AVG(response_time_ms) / 1000.0, 2)          AS avg_sec,
            ROUND(AVG(rag_score_avg)::numeric, 3)              AS rag_score
        FROM conversation_logs
        WHERE timestamp >= NOW() - INTERVAL '%s days'
        GROUP BY expert_domain
        ORDER BY count DESC
    """, (days,))


def by_model(conn, days):
    return query(conn, """
        SELECT
            model_used                                         AS model,
            COUNT(*)                                           AS uses,
            ROUND(AVG(response_time_ms) / 1000.0, 2)          AS avg_sec,
            ROUND(AVG(tokens_used))                            AS avg_tokens
        FROM conversation_logs
        WHERE timestamp >= NOW() - INTERVAL '%s days'
          AND response_time_ms IS NOT NULL
        GROUP BY model_used
        ORDER BY uses DESC
    """, (days,))


def by_prompt_version(conn):
    return query(conn, """
        SELECT
            prompt_version                                     AS version,
            expert_domain                                      AS domain,
            COUNT(*)                                           AS count,
            ROUND(AVG(response_time_ms) / 1000.0, 2)          AS avg_sec,
            SUM(CASE WHEN user_rating = 1  THEN 1 ELSE 0 END) AS positive,
            SUM(CASE WHEN user_rating = -1 THEN 1 ELSE 0 END) AS negative
        FROM conversation_logs
        GROUP BY prompt_version, expert_domain
        ORDER BY prompt_version DESC, count DESC
    """)


def top_rag_sources(conn, days):
    return query(conn, """
        SELECT
            doc->>'source'                                     AS source,
            COUNT(*)                                           AS retrievals,
            ROUND(AVG((doc->>'score')::float)::numeric, 3)    AS avg_score
        FROM conversation_logs,
             jsonb_array_elements(rag_docs) AS doc
        WHERE rag_used = TRUE
          AND timestamp >= NOW() - INTERVAL '%s days'
        GROUP BY doc->>'source'
        ORDER BY retrievals DESC
        LIMIT 15
    """, (days,))


def rag_gaps(conn, days):
    return query(conn, """
        SELECT
            expert_domain                                      AS domain,
            COUNT(*)                                           AS no_rag,
            LEFT(user_message, 80)                             AS sample
        FROM conversation_logs
        WHERE rag_used = FALSE
          AND timestamp >= NOW() - INTERVAL '%s days'
        GROUP BY expert_domain, user_message
        ORDER BY no_rag DESC
        LIMIT 10
    """, (days,))


def negative_ratings(conn):
    return query(conn, """
        SELECT
            timestamp::date                                    AS date,
            expert_domain                                      AS domain,
            prompt_version                                     AS version,
            LEFT(user_message, 70)                             AS question
        FROM conversation_logs
        WHERE user_rating = -1
        ORDER BY timestamp DESC
        LIMIT 10
    """)


def daily_trend(conn, days):
    return query(conn, """
        SELECT
            timestamp::date                                    AS day,
            COUNT(*)                                           AS conversations,
            COUNT(DISTINCT session_id)                         AS sessions,
            ROUND(AVG(response_time_ms) / 1000.0, 2)          AS avg_sec
        FROM conversation_logs
        WHERE timestamp >= NOW() - INTERVAL '%s days'
        GROUP BY timestamp::date
        ORDER BY day DESC
    """, (days,))


# ── التقرير الرئيسي ───────────────────────────────────────────────────────────

def run_report(days=30, domain="all"):
    conn = connect()
    print(f"\n{'#'*60}")
    print(f"  SaleHSaaS — تقرير تحليل المحادثات")
    print(f"  التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')} | الفترة: آخر {days} يوم")
    print(f"{'#'*60}")

    print_table(summary(conn, days),          "1. ملخص عام")
    print_table(by_domain(conn, days),        "2. الاستخدام حسب التخصص")
    print_table(by_model(conn, days),         "3. أداء النماذج")
    print_table(by_prompt_version(conn),      "4. مقارنة إصدارات البرومبت")
    print_table(top_rag_sources(conn, days),  "5. أكثر الوثائق استرجاعاً (RAG)")
    print_table(rag_gaps(conn, days),         "6. فجوات RAG (أسئلة بدون وثائق)")
    print_table(negative_ratings(conn),       "7. التقييمات السلبية")
    print_table(daily_trend(conn, min(days, 14)), "8. الاتجاه اليومي")

    conn.close()
    print(f"\n{'#'*60}")
    print("  انتهى التقرير")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SaleHSaaS Conversation Analytics")
    parser.add_argument("--days",   type=int, default=30,  help="عدد الأيام للتحليل (default: 30)")
    parser.add_argument("--domain", type=str, default="all", help="التخصص (all/n8n/legal/...)")
    args = parser.parse_args()
    run_report(days=args.days, domain=args.domain)
