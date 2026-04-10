#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Arabic Dashboard (لوحة التحكم العربية)

Main web interface for the SaleHSaaS platform.
Built with Flask, fully Arabic (RTL), and optimized for local deployment.
"""

import os
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime
from pathlib import Path
from threading import Lock

app = Flask(__name__)

# SECRET_KEY must be set via environment; fail-safe with random key in dev
_secret = os.environ.get('SECRET_KEY', '')
if not _secret:
    import secrets
    _secret = secrets.token_hex(32)
app.secret_key = _secret

# ─── CSRF Protection ─────────────────────────────────────────────────────────
csrf = CSRFProtect(app)

# Exempt JSON API endpoints (they use localhost-only enforcement)
csrf.exempt('api_status')
csrf.exempt('api_grc_scan')
csrf.exempt('api_run_agent')
csrf.exempt('api_generate_social')
csrf.exempt('api_council_sessions')
csrf.exempt('api_request_council_study')
csrf.exempt('api_dispatch_council_request')
csrf.exempt('api_council_session_decision')

# ─── Rate Limiting ────────────────────────────────────────────────────────────
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["120 per minute"],
        storage_uri="memory://",
    )
except ImportError:
    limiter = None

BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = BASE_DIR / "logs"
COUNCIL_SESSIONS_FILE = LOGS_DIR / "advisory_council_sessions.jsonl"
COUNCIL_REQUESTS_FILE = LOGS_DIR / "advisory_council_requests.jsonl"
COUNCIL_WEBHOOK_URL = os.environ.get("COUNCIL_WEBHOOK_URL", "").strip()
COUNCIL_WEBHOOK_TOKEN = os.environ.get("COUNCIL_WEBHOOK_TOKEN", "").strip()
COUNCIL_ALLOW_REMOTE = os.environ.get("COUNCIL_ALLOW_REMOTE", "false").lower() == "true"
COUNCIL_MAX_TOPIC_CHARS = int(os.environ.get("COUNCIL_MAX_TOPIC_CHARS", "1200"))
COUNCIL_REQUEST_COOLDOWN_SEC = int(os.environ.get("COUNCIL_REQUEST_COOLDOWN_SEC", "30"))
COUNCIL_ALLOWED_STUDY_TYPES = {"general", "technical", "governance", "business"}

_COUNCIL_IO_LOCK = Lock()

# ─── Platform Configuration ──────────────────────────────────────────────────
PLATFORM_CONFIG = {
    "name": "SaleHSaaS 3.0",
    "name_ar": "سالح ساس 3.0",
    "tagline": "منصة الذكاء الأعمال السيادية",
    "version": "3.0.0",
    "year": datetime.now().year
}

# ─── Mock data for dashboard (will be replaced by real data from agents) ─────
MOCK_STATS = {
    "grc_score": 87,
    "nca_score": 92,
    "pdpl_score": 85,
    "citc_score": 84,
    "active_agents": 5,
    "connected_databases": 3,
    "pending_alerts": 2,
    "last_scan": datetime.now().strftime("%Y-%m-%d %H:%M")
}

COUNCIL_MEMBERS = [
    {
        "id": "legal",
        "name": "وكيل القانون والامتثال",
        "icon": "⚖️",
        "focus": "الأنظمة، الحوكمة، الامتثال، والمخاطر التنظيمية"
    },
    {
        "id": "finance",
        "name": "وكيل المال والأعمال",
        "icon": "💰",
        "focus": "الجدوى، العائد، الأولوية، وكفاءة القرار"
    },
    {
        "id": "cyber",
        "name": "وكيل الأمن السيبراني",
        "icon": "🛡️",
        "focus": "المخاطر التقنية، PDPL، NCA، وسلامة التنفيذ"
    },
    {
        "id": "technical",
        "name": "وكيل التطوير التقني",
        "icon": "⚙️",
        "focus": "قابلية التنفيذ، التعقيد، التبعيات، وجودة المسار التقني"
    },
]


def _ensure_logs_dir() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _read_jsonl(file_path: Path) -> list[dict]:
    if not file_path.exists():
        return []

    rows: list[dict] = []
    with _COUNCIL_IO_LOCK:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def _write_jsonl(file_path: Path, rows: list[dict]) -> None:
    _ensure_logs_dir()
    with _COUNCIL_IO_LOCK:
        with file_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _append_jsonl(file_path: Path, row: dict) -> None:
    _ensure_logs_dir()
    with _COUNCIL_IO_LOCK:
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _client_ip() -> str:
    # Works for local deployment without proxy. If a proxy exists, prefer local-only runtime.
    return (request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr or "").strip()


def _is_local_client(ip: str) -> bool:
    return ip in {"127.0.0.1", "::1", "localhost"}


def _enforce_local_only() -> tuple[dict, int] | None:
    if COUNCIL_ALLOW_REMOTE:
        return None
    ip = _client_ip()
    if _is_local_client(ip):
        return None
    return ({"status": "error", "message": "الوصول إلى APIs المجلس محصور محليًا لأسباب أمنية"}, 403)


def _safe_text(value: str, limit: int) -> str:
    return (value or "").strip().replace("\x00", "")[:limit]


def _is_duplicate_recent_request(topic: str, requested_by: str) -> bool:
    rows = _read_jsonl(COUNCIL_REQUESTS_FILE)
    if not rows:
        return False

    norm_topic = " ".join(topic.split()).lower()
    now_ts = datetime.now().timestamp()

    for row in reversed(rows[-50:]):
        row_topic = " ".join(str(row.get("topic", "")).split()).lower()
        row_by = str(row.get("requested_by", ""))
        row_at = str(row.get("created_at", ""))
        if row_topic != norm_topic or row_by != requested_by:
            continue
        try:
            delta = now_ts - datetime.fromisoformat(row_at).timestamp()
            if delta <= COUNCIL_REQUEST_COOLDOWN_SEC:
                return True
        except ValueError:
            continue
    return False


def _update_jsonl_record(file_path: Path, key: str, value: str, changes: dict) -> dict | None:
    rows = _read_jsonl(file_path)
    updated = None
    for row in rows:
        if str(row.get(key)) == str(value):
            row.update(changes)
            updated = row
            break

    if updated is not None:
        _write_jsonl(file_path, rows)
    return updated


def _dispatch_request_to_workflow(record: dict) -> tuple[str, str | None]:
    if not COUNCIL_WEBHOOK_URL:
        return "queued", None

    headers = {"Content-Type": "application/json"}
    if COUNCIL_WEBHOOK_TOKEN:
        headers["Authorization"] = f"Bearer {COUNCIL_WEBHOOK_TOKEN}"

    payload = {
        "topic": record["topic"],
        "study_type": record["study_type"],
        "requested_by": record["requested_by"],
        "request_id": record["requestId"],
        "source": "arabic_dashboard",
        "created_at": record["created_at"],
    }

    try:
        response = requests.post(COUNCIL_WEBHOOK_URL, json=payload, headers=headers, timeout=180)
        response.raise_for_status()
        return "submitted_to_workflow", None
    except Exception as exc:
        return "queued", str(exc)


def _load_council_sessions(limit: int = 12) -> list[dict]:
    sessions = _read_jsonl(COUNCIL_SESSIONS_FILE)
    sessions.reverse()

    normalized = []
    for session in sessions[:limit]:
        decision_text = session.get("chairDecision", "")
        status = session.get("status")
        if not status:
            if "يعتمد" in decision_text or "اعتمد" in decision_text:
                status = "awaiting_approval"
            else:
                status = "completed"

        normalized.append({
            "session_id": session.get("sessionId", "غير معروف"),
            "session_date": session.get("sessionDate") or session.get("recordedAt", ""),
            "topic": session.get("topic", "بدون عنوان"),
            "requested_by": session.get("requestedBy", "غير محدد"),
            "chair_decision": decision_text,
            "status": status,
            "recorded_at": session.get("recordedAt", ""),
            "dashboard_decision": session.get("dashboard_decision", ""),
            "decision_updated_at": session.get("decision_updated_at", ""),
        })
    return normalized


def _load_council_requests(limit: int = 20) -> list[dict]:
    requests_rows = _read_jsonl(COUNCIL_REQUESTS_FILE)
    requests_rows.reverse()
    return requests_rows[:limit]


def _build_council_summary(sessions: list[dict], queued_requests: list[dict]) -> dict:
    awaiting_approval = sum(1 for item in sessions if item.get("status") == "awaiting_approval")
    completed_statuses = {"completed", "approved", "rejected", "restudy"}
    completed = sum(1 for item in sessions if item.get("status") in completed_statuses)
    queued = sum(1 for item in queued_requests if item.get("status") == "queued")
    in_workflow = sum(1 for item in queued_requests if item.get("status") == "submitted_to_workflow")
    latest_session = sessions[0]["session_date"] if sessions else "لا توجد جلسات بعد"
    return {
        "members": len(COUNCIL_MEMBERS),
        "sessions": len(sessions),
        "awaiting_approval": awaiting_approval,
        "queued_requests": queued,
        "submitted_to_workflow": in_workflow,
        "completed": completed,
        "latest_session": latest_session,
    }


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('dashboard.html',
                           config=PLATFORM_CONFIG,
                           stats=MOCK_STATS)


@app.route('/grc')
def grc_dashboard():
    """GRC Engine dashboard."""
    return render_template('grc.html', config=PLATFORM_CONFIG, stats=MOCK_STATS)


@app.route('/data-connector')
def data_connector():
    """Data Connector interface."""
    return render_template('data_connector.html', config=PLATFORM_CONFIG)


@app.route('/agents')
def agents():
    """AI Agents management."""
    agents_list = [
        {"id": "social_media", "name": "وكيل التسويق متعدد القنوات", "icon": "📱", "status": "نشط"},
        {"id": "financial", "name": "وكيل الذكاء المالي", "icon": "💰", "status": "مخطط"},
        {"id": "legal", "name": "وكيل الامتثال القانوني", "icon": "⚖️", "status": "مخطط"},
        {"id": "cybersecurity", "name": "وكيل الأمن السيبراني", "icon": "🛡️", "status": "مخطط"},
        {"id": "hr", "name": "وكيل الموارد البشرية", "icon": "👥", "status": "مخطط"},
    ]
    return render_template('agents.html', config=PLATFORM_CONFIG, agents=agents_list)


@app.route('/advisory-council')
def advisory_council():
    """Advisory council cockpit."""
    sessions = _load_council_sessions()
    queued_requests = _load_council_requests()
    summary = _build_council_summary(sessions, queued_requests)
    return render_template(
        'advisory_council.html',
        config=PLATFORM_CONFIG,
        members=COUNCIL_MEMBERS,
        sessions=sessions,
        queued_requests=queued_requests,
        summary=summary,
    )


@app.route('/social-media')
def social_media():
    """Social Media Management."""
    return render_template('social_media.html', config=PLATFORM_CONFIG)


@app.route('/settings')
def settings():
    """Platform settings."""
    return render_template('settings.html', config=PLATFORM_CONFIG)


# ─── API Endpoints ────────────────────────────────────────────────────────────

def _is_local_request() -> bool:
    """Check if request originates from localhost (reject external API calls)."""
    remote = request.remote_addr
    return remote in ("127.0.0.1", "::1", "localhost")

@app.before_request
def _restrict_api():
    """Block external access to API endpoints."""
    if request.path.startswith('/api/') and not _is_local_request():
        return jsonify({"error": "API access restricted to localhost"}), 403

@app.after_request
def _set_security_headers(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if 'text/html' in response.content_type:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    return response

@app.route('/api/status')
def api_status():
    """Returns the current platform status."""
    return jsonify({
        "status": "running",
        "version": PLATFORM_CONFIG["version"],
        "timestamp": datetime.now().isoformat(),
        "stats": MOCK_STATS
    })


@app.route('/api/grc/scan', methods=['POST'])
def api_grc_scan():
    """Triggers a GRC compliance scan."""
    data = request.get_json() or {}
    # In production, this would call the GRC engine
    return jsonify({
        "status": "success",
        "message": "تم بدء فحص الامتثال",
        "scan_id": f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "estimated_duration": "2-3 دقائق"
    })


@app.route('/api/agents/<agent_id>/run', methods=['POST'])
def api_run_agent(agent_id: str):
    """Runs a specific agent."""
    data = request.get_json() or {}
    return jsonify({
        "status": "success",
        "agent_id": agent_id,
        "message": f"تم تشغيل الوكيل بنجاح",
        "task_id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    })


@app.route('/api/social/generate', methods=['POST'])
def api_generate_social():
    """Generates social media content."""
    data = request.get_json() or {}
    topic = data.get('topic', 'موضوع عام')
    platform = data.get('platform', 'لينكدإن')
    return jsonify({
        "status": "success",
        "platform": platform,
        "content": f"محتوى مولّد بالذكاء الاصطناعي حول: {topic}",
        "hashtags": ["#ذكاء_اصطناعي", "#أعمال", "#سعودية"]
    })


@app.route('/api/advisory-council/sessions')
def api_council_sessions():
    """Returns council sessions and queued requests."""
    sessions = _load_council_sessions()
    queued_requests = _load_council_requests()
    return jsonify({
        "status": "success",
        "sessions": sessions,
        "queued_requests": queued_requests,
        "summary": _build_council_summary(sessions, queued_requests),
        "members": COUNCIL_MEMBERS,
    })


@app.route('/api/advisory-council/request', methods=['POST'])
@(limiter.limit("10 per minute") if limiter else (lambda f: f))
def api_request_council_study():
    """Queues a new council request from the dashboard."""
    blocked = _enforce_local_only()
    if blocked:
        payload, code = blocked
        return jsonify(payload), code

    data = request.get_json() or {}
    topic = _safe_text((data.get('topic') or ''), COUNCIL_MAX_TOPIC_CHARS)
    study_type = _safe_text((data.get('study_type') or 'general'), 32)
    requested_by = _safe_text((data.get('requested_by') or 'صالح'), 80)

    if not topic:
        return jsonify({
            "status": "error",
            "message": "الموضوع مطلوب قبل إرسال الدراسة إلى المجلس"
        }), 400

    if len(topic) < 8:
        return jsonify({
            "status": "error",
            "message": "الموضوع قصير جدًا. اكتب وصفًا أوضح للفكرة"
        }), 400

    if study_type not in COUNCIL_ALLOWED_STUDY_TYPES:
        return jsonify({
            "status": "error",
            "message": "نوع الدراسة غير معتمد"
        }), 400

    if _is_duplicate_recent_request(topic, requested_by):
        return jsonify({
            "status": "error",
            "message": f"تم إرسال طلب مشابه قبل أقل من {COUNCIL_REQUEST_COOLDOWN_SEC} ثانية. انتظر قليلًا ثم أعد المحاولة"
        }), 429

    _ensure_logs_dir()
    record = {
        "requestId": f"REQ-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "topic": topic,
        "study_type": study_type,
        "requested_by": requested_by,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "delivery_error": None,
    }

    status, delivery_error = _dispatch_request_to_workflow(record)
    record["status"] = status
    record["delivery_error"] = delivery_error

    _append_jsonl(COUNCIL_REQUESTS_FILE, record)

    return jsonify({
        "status": "success",
        "message": "تم تسجيل الطلب وإرساله إلى مسار المجلس الاستشاري" if status == "submitted_to_workflow" else "تم تسجيل الطلب محلياً بانتظار ربط workflow أو إعادة الإرسال",
        "request": record,
    })


@app.route('/api/advisory-council/request/<request_id>/dispatch', methods=['POST'])
@(limiter.limit("10 per minute") if limiter else (lambda f: f))
def api_dispatch_council_request(request_id: str):
    """Retries sending a queued request to the workflow."""
    blocked = _enforce_local_only()
    if blocked:
        payload, code = blocked
        return jsonify(payload), code

    rows = _read_jsonl(COUNCIL_REQUESTS_FILE)
    request_row = next((row for row in rows if str(row.get("requestId")) == request_id), None)
    if request_row is None:
        return jsonify({"status": "error", "message": "تعذر العثور على الطلب المطلوب"}), 404

    status, delivery_error = _dispatch_request_to_workflow(request_row)
    updated = _update_jsonl_record(
        COUNCIL_REQUESTS_FILE,
        "requestId",
        request_id,
        {
            "status": status,
            "delivery_error": delivery_error,
            "last_dispatch_at": datetime.now().isoformat(),
        },
    )

    return jsonify({
        "status": "success",
        "message": "أعيد إرسال الطلب إلى workflow بنجاح" if status == "submitted_to_workflow" else "تعذر إرسال الطلب إلى workflow، بقي الطلب في الطابور المحلي",
        "request": updated,
    })


@app.route('/api/advisory-council/session/<session_id>/decision', methods=['POST'])
@(limiter.limit("10 per minute") if limiter else (lambda f: f))
def api_council_session_decision(session_id: str):
    """Stores dashboard approval/reject/restudy decisions for a session."""
    blocked = _enforce_local_only()
    if blocked:
        payload, code = blocked
        return jsonify(payload), code

    data = request.get_json() or {}
    decision = (data.get("decision") or "").strip().lower()
    notes = _safe_text((data.get("notes") or ""), 500)

    decision_map = {
        "approve": ("approved", "اعتماد من الشاشة"),
        "reject": ("rejected", "رفض من الشاشة"),
        "restudy": ("restudy", "إعادة دراسة من الشاشة"),
    }

    if decision not in decision_map:
        return jsonify({"status": "error", "message": "قرار غير صالح"}), 400

    status_value, decision_label = decision_map[decision]
    updated = _update_jsonl_record(
        COUNCIL_SESSIONS_FILE,
        "sessionId",
        session_id,
        {
            "status": status_value,
            "dashboard_decision": decision_label,
            "decision_notes": notes,
            "decision_updated_at": datetime.now().isoformat(),
        },
    )

    if updated is None:
        return jsonify({"status": "error", "message": "تعذر العثور على الجلسة المطلوبة"}), 404

    return jsonify({
        "status": "success",
        "message": f"تم تسجيل القرار: {decision_label}",
        "session": updated,
    })


if __name__ == '__main__':
    port = int(os.environ.get('DASHBOARD_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"🚀 SaleHSaaS Dashboard running on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
