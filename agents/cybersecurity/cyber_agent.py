#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 4.0 - Cybersecurity Agent (وكيل الأمن السيبراني)
المسؤول عن تحليل تقارير الامتثال والرد على استفسارات المستخدم الأمنية.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

class CybersecurityAgent:
    """
    وكيل ذكاء اصطناعي متخصص في الأمن السيبراني والامتثال لأنظمة NCA و PDPL.
    """

    def __init__(self, ollama_url: str = "http://host.docker.internal:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        self.reports_dir = Path("/mnt/workspace/iumDLdMeLEk8LXJooJDdK1u4FnvzMAiga1jTUcLZEz/core/grc_engine/reports")

    def get_latest_grc_report(self):
        """قراءة أحدث تقرير امتثال مولد"""
        if not self.reports_dir.exists():
            return None
        reports = sorted(self.reports_dir.glob("GRC_Report_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not reports:
            return None
        with open(reports[0], 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_security_status(self, user_query: str):
        """تحليل حالة الأمن والرد على المستخدم باستخدام LLM"""
        report_data = self.get_latest_grc_report()
        
        context = ""
        if report_data:
            context = f"نتائج فحص الامتثال الأخير:\n{json.dumps(report_data, ensure_ascii=False, indent=2)}"
        else:
            context = "لا توجد تقارير امتثال سابقة. يجب تشغيل فحص الامتثال أولاً."

        prompt = f"""أنت 'وكيل الأمن السيبراني' في منصة SaleH SaaS 4.0.
مهمتك هي مساعدة المستخدم في فهم حالة الأمن والامتثال بناءً على التقارير.

السياق الحالي:
{context}

سؤال المستخدم: {user_query}

أجب باللغة العربية الفصحى، بأسلوب مهني وتقني دقيق. إذا وجدت مخاطر حرجة، نبه المستخدم إليها فوراً وقدم توصيات بناءً على ضوابط الهيئة الوطنية للأمن السيبراني (NCA) ونظام حماية البيانات الشخصية (PDPL).
"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            return response.json().get("response", "عذراً، حدث خطأ في توليد الإجابة.")
        except Exception as e:
            return f"خطأ في الاتصال بمحرك الذكاء الاصطناعي: {str(e)}"

if __name__ == '__main__':
    agent = CybersecurityAgent()
    # تجربة تحليل
    print("--- فحص حالة الأمن ---")
    print(agent.analyze_security_status("ما هي حالة الامتثال الحالية وما هي أهم المخاطر؟"))
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
