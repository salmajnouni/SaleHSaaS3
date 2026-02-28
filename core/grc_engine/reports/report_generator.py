#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GRC Report Generator

Generates compliance reports in various formats.
"""

from datetime import datetime

class GRCReportGenerator:
    """Generates GRC reports from assessment results."""

    def generate_markdown_report(self, results, output_path):
        """
        Generates a GRC compliance report in Markdown format.

        Args:
            results (dict): The assessment results from the GRC_Engine.
            output_path (str): The path to save the Markdown file.
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 🛡️ تقرير امتثال الحوكمة والمخاطر (GRC) - SaleHSaaS 3.0\n\n")
            f.write(f"**تاريخ التقرير:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## ملخص النتائج\n\n")

            summary_table = "| الإطار التنظيمي | الحالة | عدد الملاحظات |\n"
                            "| :--- | :--- | :--- |\n"

            for framework, result in results.items():
                status_ar = "🟢 متوافق" if result['status'] == "Compliant" else "🔴 غير مكتمل"
                findings_count = len(result['findings'])
                summary_table += f"| {result['framework']} | {status_ar} | {findings_count} |\n"

            f.write(summary_table)
            f.write("\n---\n\n## التفاصيل\n\n")

            for framework, result in results.items():
                f.write(f"### {result['framework']}\n\n")
                if not result['findings']:
                    f.write("✅ لم يتم العثور على ملاحظات.\n\n")
                    continue

                findings_table = "| المعرف | الوصف | الخطورة |\n"
                                 "| :--- | :--- | :--- |\n"

                for finding in result['findings']:
                    severity_map = {
                        "Critical": "حرجة",
                        "High": "عالية",
                        "Medium": "متوسطة",
                        "Low": "منخفضة"
                    }
                    severity_ar = severity_map.get(finding['severity'], finding['severity'])
                    findings_table += f"| {finding['control_id']} | {finding['description']} | {severity_ar} |\n"

                f.write(findings_table)
                f.write("\n")

        print(f"Markdown report generated at {output_path}")
