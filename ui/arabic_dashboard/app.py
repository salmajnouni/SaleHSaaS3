#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Arabic Dashboard (لوحة التحكم العربية)

Main web interface for the SaleHSaaS platform.
Built with Flask, fully Arabic (RTL), and optimized for local deployment.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'salehsaas-dev-key-change-in-production')

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
        {"id": "financial", "name": "وكيل الذكاء المالي", "icon": "💰", "status": "نشط"},
        {"id": "legal", "name": "وكيل الامتثال القانوني", "icon": "⚖️", "status": "نشط"},
        {"id": "cybersecurity", "name": "وكيل الأمن السيبراني", "icon": "🛡️", "status": "نشط"},
        {"id": "social_media", "name": "وكيل التواصل الاجتماعي", "icon": "📱", "status": "نشط"},
        {"id": "hr", "name": "وكيل الموارد البشرية", "icon": "👥", "status": "نشط"},
    ]
    return render_template('agents.html', config=PLATFORM_CONFIG, agents=agents_list)


@app.route('/social-media')
def social_media():
    """Social Media Management."""
    return render_template('social_media.html', config=PLATFORM_CONFIG)


@app.route('/settings')
def settings():
    """Platform settings."""
    return render_template('settings.html', config=PLATFORM_CONFIG)


# ─── API Endpoints ────────────────────────────────────────────────────────────

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


if __name__ == '__main__':
    port = int(os.environ.get('DASHBOARD_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"🚀 SaleHSaaS Dashboard running on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
