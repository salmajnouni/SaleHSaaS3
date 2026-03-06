"""
conversation_logger.py — SaleHSaaS v2.1.0
وحدة التسجيل المشتركة لكل الـ Pipelines الخبيرة

تُسجِّل كل محادثة في PostgreSQL تلقائياً:
- نص السؤال والإجابة
- التخصص والنموذج المستخدم
- أداء RAG (الوثائق المسترجعة + درجة الصلة)
- وقت الاستجابة وعدد التوكنز
- إصدار البرومبت

الاستخدام:
    from conversation_logger import ConversationLogger
    logger = ConversationLogger()
    log_id = logger.log(...)
"""

import os
import time
import json
import uuid
import threading
from typing import Optional, List, Dict, Any

# psycopg2 اختياري — إذا لم يكن مثبتاً يعمل النظام بدون تسجيل
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class ConversationLogger:
    """
    مسجّل المحادثات — يعمل بشكل غير متزامن (non-blocking)
    لا يؤثر على وقت استجابة الـ Pipeline حتى لو فشل الاتصال بـ PostgreSQL
    """

    def __init__(self):
        self._conn = None
        self._lock = threading.Lock()
        self._enabled = PSYCOPG2_AVAILABLE
        self._db_config = {
            "host":     os.getenv("POSTGRES_HOST",     "postgres"),
            "port":     int(os.getenv("POSTGRES_PORT", "5432")),
            "dbname":   os.getenv("POSTGRES_DB",       "salehsaas"),
            "user":     os.getenv("POSTGRES_USER",     "salehsaas"),
            "password": os.getenv("POSTGRES_PASSWORD", "salehsaas_pass"),
            "connect_timeout": 3,
            "application_name": "salehsaas_pipelines",
        }

    # ── اتصال قاعدة البيانات ──────────────────────────────────────────────────

    def _get_conn(self):
        """يُعيد اتصالاً صالحاً أو None إذا تعذّر الاتصال"""
        if not self._enabled:
            return None
        try:
            if self._conn is None or self._conn.closed:
                self._conn = psycopg2.connect(**self._db_config)
                self._conn.autocommit = True
            return self._conn
        except Exception as e:
            print(f"[ConversationLogger] DB connection failed: {e}")
            self._conn = None
            return None

    # ── التسجيل الرئيسي ───────────────────────────────────────────────────────

    def log(
        self,
        *,
        session_id:       Optional[str]        = None,
        user_message:     str,
        assistant_reply:  str,
        expert_domain:    str,
        model_used:       str,
        prompt_version:   str                  = "2.0.0",
        rag_used:         bool                 = False,
        rag_docs:         Optional[List[Dict]] = None,
        response_time_ms: Optional[int]        = None,
        tokens_used:      Optional[int]        = None,
        user_rating:      Optional[int]        = None,
        extra:            Optional[Dict]        = None,
    ) -> Optional[str]:
        """
        يسجّل محادثة واحدة في قاعدة البيانات.

        Parameters
        ----------
        session_id       : معرّف الجلسة (UUID) — يُنشأ تلقائياً إذا لم يُعطَ
        user_message     : نص سؤال المستخدم
        assistant_reply  : نص إجابة المساعد
        expert_domain    : التخصص (n8n / legal / financial / hr / cybersecurity / social_media / general)
        model_used       : اسم النموذج (qwen2.5:7b / deepseek-r1:7b)
        prompt_version   : إصدار البرومبت (2.0.0)
        rag_used         : هل استُخدم RAG؟
        rag_docs         : قائمة الوثائق المسترجعة [{source, score, snippet}]
        response_time_ms : وقت الاستجابة بالميلي ثانية
        tokens_used      : عدد التوكنز المستخدمة (تقريبي)
        user_rating      : تقييم المستخدم (1 = جيد، -1 = سيء، None = لم يُقيَّم)
        extra            : بيانات إضافية اختيارية (JSONB)

        Returns
        -------
        str | None : معرّف السجل (UUID) أو None إذا فشل التسجيل
        """
        if not self._enabled:
            return None

        # حساب متوسط درجة صلة RAG
        rag_score_avg = None
        if rag_docs:
            scores = [d.get("score", 0) for d in rag_docs if "score" in d]
            if scores:
                rag_score_avg = round(sum(scores) / len(scores), 4)

        # تقدير عدد التوكنز إذا لم يُعطَ
        if tokens_used is None:
            tokens_used = (len(user_message) + len(assistant_reply)) // 4

        record_id = str(uuid.uuid4())
        if session_id is None:
            session_id = str(uuid.uuid4())

        # تسجيل غير متزامن — لا يُوقف الـ Pipeline
        thread = threading.Thread(
            target=self._insert,
            args=(
                record_id, session_id, user_message, assistant_reply,
                expert_domain, model_used, prompt_version,
                rag_used, rag_docs, rag_score_avg,
                response_time_ms, tokens_used, user_rating, extra,
            ),
            daemon=True,
        )
        thread.start()
        return record_id

    def _insert(
        self,
        record_id, session_id, user_message, assistant_reply,
        expert_domain, model_used, prompt_version,
        rag_used, rag_docs, rag_score_avg,
        response_time_ms, tokens_used, user_rating, extra,
    ):
        """تنفيذ INSERT في thread منفصل"""
        with self._lock:
            conn = self._get_conn()
            if conn is None:
                return
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO conversation_logs (
                            id, session_id,
                            user_message, assistant_reply,
                            expert_domain, model_used, prompt_version,
                            rag_used, rag_docs, rag_score_avg,
                            response_time_ms, tokens_used,
                            user_rating, extra
                        ) VALUES (
                            %s, %s,
                            %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s
                        )
                        """,
                        (
                            record_id, session_id,
                            user_message[:10000], assistant_reply[:20000],
                            expert_domain, model_used, prompt_version,
                            rag_used,
                            json.dumps(rag_docs or [], ensure_ascii=False),
                            rag_score_avg,
                            response_time_ms, tokens_used,
                            user_rating,
                            json.dumps(extra or {}, ensure_ascii=False),
                        ),
                    )
            except Exception as e:
                print(f"[ConversationLogger] Insert failed: {e}")
                self._conn = None  # إعادة الاتصال في المرة القادمة

    # ── تحديث تقييم المستخدم ─────────────────────────────────────────────────

    def rate(self, record_id: str, rating: int) -> bool:
        """
        يُحدِّث تقييم المستخدم لمحادثة سابقة.
        rating: 1 (إيجابي) أو -1 (سلبي)
        """
        if not self._enabled:
            return False
        conn = self._get_conn()
        if conn is None:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversation_logs SET user_rating = %s WHERE id = %s",
                    (rating, record_id),
                )
            return True
        except Exception as e:
            print(f"[ConversationLogger] Rate update failed: {e}")
            return False


# ── مساعد قياس الوقت ─────────────────────────────────────────────────────────

class Timer:
    """مؤقت بسيط لقياس وقت الاستجابة"""

    def __init__(self):
        self._start = time.monotonic()

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self._start) * 1000)


# ── singleton مشترك بين كل الـ Pipelines ────────────────────────────────────

_logger_instance: Optional[ConversationLogger] = None

def get_logger() -> ConversationLogger:
    """يُعيد instance واحد مشترك (singleton)"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ConversationLogger()
    return _logger_instance
