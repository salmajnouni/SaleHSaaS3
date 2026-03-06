-- ============================================================
-- analyze_conversations.sql — SaleHSaaS v2.1.0
-- استعلامات تحليل المحادثات للتحسين المستمر
-- الاستخدام: psql -U salehsaas -d salehsaas -f analyze_conversations.sql
-- ============================================================

-- ── 1. ملخص عام (آخر 7 أيام) ─────────────────────────────────────────────────
\echo '=== ملخص عام — آخر 7 أيام ==='
SELECT
    COUNT(*)                                        AS total_conversations,
    COUNT(DISTINCT session_id)                      AS unique_sessions,
    ROUND(AVG(response_time_ms) / 1000.0, 2)       AS avg_response_sec,
    ROUND(AVG(tokens_used))                         AS avg_tokens,
    SUM(CASE WHEN rag_used THEN 1 ELSE 0 END)       AS rag_used_count,
    ROUND(100.0 * SUM(CASE WHEN rag_used THEN 1 ELSE 0 END) / COUNT(*), 1) AS rag_usage_pct
FROM conversation_logs
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- ── 2. توزيع الاستخدام حسب التخصص ───────────────────────────────────────────
\echo ''
\echo '=== الاستخدام حسب التخصص ==='
SELECT
    expert_domain,
    COUNT(*)                                        AS conversations,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct,
    ROUND(AVG(response_time_ms) / 1000.0, 2)       AS avg_sec,
    ROUND(AVG(rag_score_avg)::numeric, 3)           AS avg_rag_score
FROM conversation_logs
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY expert_domain
ORDER BY conversations DESC;

-- ── 3. أداء النماذج ──────────────────────────────────────────────────────────
\echo ''
\echo '=== أداء النماذج ==='
SELECT
    model_used,
    COUNT(*)                                        AS uses,
    ROUND(AVG(response_time_ms) / 1000.0, 2)       AS avg_sec,
    MIN(response_time_ms / 1000.0)                  AS min_sec,
    MAX(response_time_ms / 1000.0)                  AS max_sec,
    ROUND(AVG(tokens_used))                         AS avg_tokens
FROM conversation_logs
WHERE timestamp >= NOW() - INTERVAL '30 days'
  AND response_time_ms IS NOT NULL
GROUP BY model_used
ORDER BY uses DESC;

-- ── 4. تحليل إصدارات البرومبت (قبل/بعد التحديث) ─────────────────────────────
\echo ''
\echo '=== مقارنة إصدارات البرومبت ==='
SELECT
    prompt_version,
    expert_domain,
    COUNT(*)                                        AS conversations,
    ROUND(AVG(response_time_ms) / 1000.0, 2)       AS avg_sec,
    ROUND(AVG(rag_score_avg)::numeric, 3)           AS avg_rag_score,
    SUM(CASE WHEN user_rating = 1  THEN 1 ELSE 0 END) AS positive_ratings,
    SUM(CASE WHEN user_rating = -1 THEN 1 ELSE 0 END) AS negative_ratings
FROM conversation_logs
GROUP BY prompt_version, expert_domain
ORDER BY prompt_version DESC, conversations DESC;

-- ── 5. جودة RAG — الوثائق الأكثر استرجاعاً ──────────────────────────────────
\echo ''
\echo '=== أكثر الوثائق استرجاعاً في RAG ==='
SELECT
    doc->>'source'                                  AS source,
    COUNT(*)                                        AS retrieval_count,
    ROUND(AVG((doc->>'score')::float)::numeric, 3) AS avg_score
FROM conversation_logs,
     jsonb_array_elements(rag_docs) AS doc
WHERE rag_used = TRUE
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY doc->>'source'
ORDER BY retrieval_count DESC
LIMIT 20;

-- ── 6. الأسئلة بدون RAG (فجوات في قاعدة المعرفة) ────────────────────────────
\echo ''
\echo '=== محادثات بدون RAG (فجوات محتملة في قاعدة المعرفة) ==='
SELECT
    expert_domain,
    COUNT(*)                                        AS no_rag_count,
    LEFT(user_message, 100)                         AS sample_question
FROM conversation_logs
WHERE rag_used = FALSE
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY expert_domain, user_message
ORDER BY no_rag_count DESC
LIMIT 15;

-- ── 7. أبطأ الاستجابات (لتحسين الأداء) ──────────────────────────────────────
\echo ''
\echo '=== أبطأ 10 استجابات ==='
SELECT
    timestamp::date                                 AS date,
    expert_domain,
    model_used,
    ROUND(response_time_ms / 1000.0, 1)            AS seconds,
    LEFT(user_message, 80)                          AS question
FROM conversation_logs
WHERE response_time_ms IS NOT NULL
ORDER BY response_time_ms DESC
LIMIT 10;

-- ── 8. التقييمات السلبية (للمراجعة الفورية) ─────────────────────────────────
\echo ''
\echo '=== التقييمات السلبية ==='
SELECT
    timestamp,
    expert_domain,
    model_used,
    prompt_version,
    LEFT(user_message, 100)                         AS question,
    LEFT(assistant_reply, 200)                      AS reply_preview
FROM conversation_logs
WHERE user_rating = -1
ORDER BY timestamp DESC
LIMIT 20;

-- ── 9. اتجاه الاستخدام اليومي (آخر 14 يوم) ──────────────────────────────────
\echo ''
\echo '=== الاستخدام اليومي ==='
SELECT
    timestamp::date                                 AS day,
    COUNT(*)                                        AS conversations,
    COUNT(DISTINCT session_id)                      AS sessions,
    ROUND(AVG(response_time_ms) / 1000.0, 2)       AS avg_sec
FROM conversation_logs
WHERE timestamp >= NOW() - INTERVAL '14 days'
GROUP BY timestamp::date
ORDER BY day DESC;
