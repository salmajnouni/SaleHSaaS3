#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - GRC Engine

Main engine for Governance, Risk, and Compliance.
Orchestrates compliance checks against NCA, PDPL, and CITC regulations.
"""

import json
import os
import sys
from datetime import datetime

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nca.nca_checker import NCAComplianceChecker
from pdpl.pdpl_checker import PDPLComplianceChecker
from citc.citc_checker import CITCComplianceChecker
from reports.report_generator import GRCReportGenerator

import argparse

class GRC_Engine:
    """Manages and runs GRC compliance checks."""

    def __init__(self, config_path="config/grc_config.json"):
        """Initializes the GRC Engine with necessary checkers."""
        self.nca_checker = NCAComplianceChecker()
        self.pdpl_checker = PDPLComplianceChecker()
        self.citc_checker = CITCComplianceChecker()
        self.report_generator = GRCReportGenerator()
        self.results = {}

    def monitor_logs(self, log_path):
        """
        Scans a specific log file for immediate security/compliance violations.
        Used by n8n for automated monitoring.
        """
        print(f"Monitoring log file: {log_path}")
        if not os.path.exists(log_path):
            print(f"Error: Log file {log_path} not found.")
            return {"status": "error", "message": "Log file not found"}

        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-100:] # Check last 100 lines

        violations = []
        for line in lines:
            # Simple violation detection patterns
            if "FAIL" in line or "error" in line.upper() or "blocked" in line.upper():
                violations.append(line.strip())
            if "National ID" in line or "IBAN" in line:
                violations.append(f"PII Leak Detected: {line.strip()}")

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "violations_found": len(violations),
            "findings": violations
        }

    def run_full_assessment(self, data_sources):
        """
        Runs a full GRC assessment across all frameworks.
        """
        print("Starting Full GRC Assessment...")

        # Run NCA Assessment
        print("Running NCA Compliance Check...")
        nca_results = self.nca_checker.run_checks(data_sources.get("system_logs", []))
        self.results["nca"] = nca_results
        print(f"NCA Check Complete. Found {len(nca_results['findings'])} findings.")

        # Run PDPL Assessment
        print("Running PDPL Compliance Check...")
        pdpl_results = self.pdpl_checker.run_checks(data_sources.get("databases", []))
        self.results["pdpl"] = pdpl_results
        print(f"PDPL Check Complete. Found {len(pdpl_results['findings'])} findings.")

        # Run CITC Assessment
        print("Running CITC Compliance Check...")
        citc_results = self.citc_checker.run_checks(data_sources.get("network_traffic", []))
        self.results["citc"] = citc_results
        print(f"CITC Check Complete. Found {len(citc_results['findings'])} findings.")

        print("Full GRC Assessment Finished.")
        return self.results

    def generate_report(self, report_format="md"):
        """
        Generates a compliance report.
        """
        if not self.results:
            print("No assessment has been run. Please run an assessment first.")
            return None

        print(f"Generating GRC report in {report_format} format...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"GRC_Report_{timestamp}.{report_format}")

        if report_format == "md":
            self.report_generator.generate_markdown_report(self.results, report_path)
        elif report_format == "json":
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=4)
        else:
            print(f"Report format '{report_format}' not supported.")
            return None

        print(f"Report generated successfully at: {report_path}")
        return report_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SaleH GRC Engine CLI")
    parser.add_argument("--mode", choices=["full", "monitor"], default="full", help="Operation mode")
    parser.add_argument("--log", type=str, help="Log file path for monitor mode")
    args = parser.parse_args()

    engine = GRC_Engine()

    if args.mode == "monitor":
        if not args.log:
            print("Error: --log path required for monitor mode")
            sys.exit(1)
        res = engine.monitor_logs(args.log)
        print(json.dumps(res, indent=4, ensure_ascii=False))
        # Exit with 1 if violations found to trigger n8n alerts
        sys.exit(1 if res["violations_found"] > 0 else 0)

    # Default Full Assessment
    mock_data = {
        "system_logs": ["/mnt/workspace/iumDLdMeLEk8LXJooJDdK1u4FnvzMAiga1jTUcLZEz/logs/watcher.log"],
        "databases": ["postgresql://salehsaas:salehsaas_pass@postgres:5432/salehsaas"],
        "network_traffic": ["path/to/traffic.pcap"]
    }
    assessment_results = engine.run_full_assessment(mock_data)
    engine.generate_report(report_format="md")
    engine.generate_report(report_format="json")
