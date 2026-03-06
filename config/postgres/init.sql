-- SaleHSaaS 3.0 - Database Initialization
-- تهيئة قاعدة البيانات الرئيسية

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ── GRC Tables ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS grc_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_type VARCHAR(50) NOT NULL,  -- 'NCA', 'PDPL', 'CITC', 'FULL'
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    overall_score DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed'
    results JSONB,
    created_by VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS grc_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES grc_scans(id),
    framework VARCHAR(50) NOT NULL,  -- 'NCA', 'PDPL', 'CITC'
    control_id VARCHAR(20),
    control_name VARCHAR(200),
    severity VARCHAR(20),  -- 'critical', 'high', 'medium', 'low'
    status VARCHAR(30),    -- 'compliant', 'non_compliant', 'partial'
    description TEXT,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── Agent Tasks ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL,  -- 'financial', 'legal', 'cybersecurity', etc.
    task_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── Data Connections ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS data_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    connection_type VARCHAR(50) NOT NULL,  -- 'postgresql', 'mysql', 'mssql', 'oracle', 'sap', 'api'
    host VARCHAR(255),
    port INTEGER,
    database_name VARCHAR(100),
    username VARCHAR(100),
    -- Password stored encrypted, never in plaintext
    connection_params JSONB,
    is_active BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMP,
    last_test_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ── Social Media Content ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS social_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,
    topic VARCHAR(500),
    content_type VARCHAR(50),
    post_text TEXT,
    hashtags TEXT[],
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'scheduled', 'published'
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    ai_model_used VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── Audit Log ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_grc_scans_type ON grc_scans(scan_type);
CREATE INDEX IF NOT EXISTS idx_grc_scans_status ON grc_scans(status);
CREATE INDEX IF NOT EXISTS idx_grc_findings_scan ON grc_findings(scan_id);
CREATE INDEX IF NOT EXISTS idx_grc_findings_severity ON grc_findings(severity);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_type ON agent_tasks(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_social_content_platform ON social_content(platform);
CREATE INDEX IF NOT EXISTS idx_social_content_status ON social_content(status);

-- ── Initial Data ──────────────────────────────────────────────────────────────

INSERT INTO data_connections (name, connection_type, host, port, database_name, username, is_active)
VALUES ('قاعدة البيانات المحلية', 'postgresql', 'postgres', 5432, 'salehsaas', 'salehsaas_user', true)
ON CONFLICT DO NOTHING;

-- ── Conversation Logs (Pipeline Monitoring & Continuous Improvement) ────────

CREATE TABLE IF NOT EXISTS conversation_logs (
    id               UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id       UUID,
    timestamp        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- المحادثة
    user_message     TEXT         NOT NULL,
    assistant_reply  TEXT         NOT NULL,
    expert_domain    VARCHAR(50)  NOT NULL,  -- n8n/legal/financial/hr/cybersecurity/social_media/general/orchestrator
    model_used       VARCHAR(100) NOT NULL,  -- qwen2.5:7b / deepseek-r1:7b

    -- إصدار البرومبت (للتحسين المستمر)
    prompt_version   VARCHAR(20)  NOT NULL DEFAULT '2.1.0',

    -- جودة RAG
    rag_used         BOOLEAN      NOT NULL DEFAULT FALSE,
    rag_docs         JSONB,                 -- [{source, score, snippet}]
    rag_score_avg    FLOAT,                 -- متوسط درجة صلة الوثائق المسترجعة

    -- الأداء
    response_time_ms INTEGER,               -- وقت الاستجابة بالميلي ثانية
    tokens_used      INTEGER,               -- عدد التوكنز (تقريبي)

    -- تقييم المستخدم (يُملأ لاحقاً إذا أُضيف زر التقييم)
    user_rating      SMALLINT,              -- 1 = جيد | -1 = سيء | NULL = لم يُقيَّم

    -- بيانات إضافية سياقية
    extra            JSONB
);

-- Indexes للاستعلامات الشائعة
CREATE INDEX IF NOT EXISTS idx_conv_timestamp  ON conversation_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conv_domain     ON conversation_logs(expert_domain);
CREATE INDEX IF NOT EXISTS idx_conv_model      ON conversation_logs(model_used);
CREATE INDEX IF NOT EXISTS idx_conv_prompt_ver ON conversation_logs(prompt_version);
CREATE INDEX IF NOT EXISTS idx_conv_rag_used   ON conversation_logs(rag_used);
CREATE INDEX IF NOT EXISTS idx_conv_rating     ON conversation_logs(user_rating) WHERE user_rating IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_conv_session    ON conversation_logs(session_id);

-- ── n8n Database ────────────────────────────────────────────────────────────

SELECT 'CREATE DATABASE n8n'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'n8n')\gexec

-- Completion message
DO $$ BEGIN
    RAISE NOTICE 'SaleHSaaS database initialized successfully';
END $$;
