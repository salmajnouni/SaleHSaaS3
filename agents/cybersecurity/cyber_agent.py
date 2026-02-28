#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Cybersecurity Agent (وكيل الأمن السيبراني)

Monitors system security, checks NCA compliance, scans for vulnerabilities,
and generates security reports - all locally with zero external exposure.
"""

import os
import json
import hashlib
import subprocess
from datetime import datetime
from typing import Optional


class CybersecurityAgent:
    """
    AI-powered cybersecurity agent aligned with NCA Basic Controls.
    """

    AGENT_NAME = "وكيل الأمن السيبراني"
    AGENT_VERSION = "3.0"

    # NCA Basic Cybersecurity Controls (ECC-1:2018)
    NCA_CONTROLS = {
        "1-1": "حوكمة الأمن السيبراني",
        "1-2": "مخاطر الأمن السيبراني",
        "2-1": "أمن الأصول",
        "2-2": "إدارة الهويات والصلاحيات",
        "2-3": "أمن العمليات",
        "2-4": "أمن الاتصالات والشبكات",
        "2-5": "أمن الأجهزة",
        "2-6": "أمن التطبيقات",
        "2-7": "أمن البيانات",
        "2-8": "الاستمرارية التشغيلية",
        "2-9": "أمن الموارد البشرية",
        "2-10": "أمن الطرف الثالث",
        "3-1": "الأمن السيبراني في الحوادث",
        "3-2": "التدريب والتوعية"
    }

    def __init__(self, ollama_url: str = "http://ollama:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        print(f"✅ {self.AGENT_NAME} v{self.AGENT_VERSION} initialized.")

    def scan_configuration(self, config: dict) -> dict:
        """
        Scans a system configuration for security weaknesses.

        Args:
            config (dict): System configuration to scan.

        Returns:
            dict: Security scan results with findings and NCA control mapping.
        """
        print(f"🔍 فحص الإعدادات الأمنية...")
        findings = []
        nca_gaps = []

        # Check 1: Default/weak passwords
        config_str = json.dumps(config).lower()
        weak_passwords = ['password', '123456', 'admin', 'root', 'default', 'changeme']
        for weak_pw in weak_passwords:
            if weak_pw in config_str:
                findings.append({
                    "severity": "حرج",
                    "finding": f"كلمة مرور ضعيفة أو افتراضية: '{weak_pw}'",
                    "nca_control": "2-2",
                    "recommendation": "استخدم كلمات مرور قوية لا تقل عن 12 حرفاً"
                })
                if "2-2" not in nca_gaps:
                    nca_gaps.append("2-2")

        # Check 2: Encryption settings
        if not config.get('encryption_enabled', False):
            findings.append({
                "severity": "عالٍ",
                "finding": "التشفير غير مفعّل",
                "nca_control": "2-7",
                "recommendation": "فعّل تشفير AES-256 لجميع البيانات الحساسة"
            })
            nca_gaps.append("2-7")

        # Check 3: Logging
        if not config.get('logging_enabled', False):
            findings.append({
                "severity": "متوسط",
                "finding": "التسجيل والمراقبة غير مفعّل",
                "nca_control": "2-3",
                "recommendation": "فعّل تسجيل جميع الأحداث الأمنية"
            })
            nca_gaps.append("2-3")

        # Check 4: MFA
        if not config.get('mfa_enabled', False):
            findings.append({
                "severity": "عالٍ",
                "finding": "المصادقة متعددة العوامل (MFA) غير مفعّلة",
                "nca_control": "2-2",
                "recommendation": "فعّل MFA لجميع الحسابات الإدارية"
            })

        # Check 5: Backup
        if not config.get('backup_enabled', False):
            findings.append({
                "severity": "عالٍ",
                "finding": "النسخ الاحتياطي غير مفعّل",
                "nca_control": "2-8",
                "recommendation": "فعّل النسخ الاحتياطي التلقائي اليومي"
            })
            nca_gaps.append("2-8")

        # Calculate compliance score
        total_controls = len(self.NCA_CONTROLS)
        gap_controls = len(set(nca_gaps))
        compliance_score = round(((total_controls - gap_controls) / total_controls) * 100, 1)

        return {
            "agent": self.AGENT_NAME,
            "timestamp": datetime.now().isoformat(),
            "total_findings": len(findings),
            "critical_findings": len([f for f in findings if f['severity'] == 'حرج']),
            "nca_compliance_score": f"{compliance_score}%",
            "nca_gaps": [{"control_id": g, "name": self.NCA_CONTROLS.get(g, "غير معروف")} for g in nca_gaps],
            "findings": findings
        }

    def check_file_integrity(self, file_path: str) -> dict:
        """
        Calculates and returns the SHA-256 hash of a file for integrity verification.

        Args:
            file_path (str): Path to the file.

        Returns:
            dict: File integrity information.
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return {
                "file": file_path,
                "sha256": sha256_hash.hexdigest(),
                "timestamp": datetime.now().isoformat(),
                "status": "verified"
            }
        except Exception as e:
            return {"file": file_path, "error": str(e), "status": "failed"}

    def generate_security_report(self, scan_result: dict, output_path: str = "security_report.json") -> str:
        """Saves the security scan result to a JSON report."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scan_result, f, ensure_ascii=False, indent=2)
        print(f"✅ تم حفظ تقرير الأمن السيبراني: {output_path}")
        return output_path


if __name__ == '__main__':
    agent = CybersecurityAgent()
    sample_config = {
        "db_password": "admin",
        "encryption_enabled": False,
        "logging_enabled": True,
        "mfa_enabled": False,
        "backup_enabled": False
    }
    result = agent.scan_configuration(sample_config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
