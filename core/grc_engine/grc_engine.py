#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - GRC Engine

Main engine for Governance, Risk, and Compliance.
Orchestrates compliance checks against NCA, PDPL, and CITC regulations.
"""

import json
import os
from datetime import datetime

from .nca.nca_checker import NCAComplianceChecker
from .pdpl.pdpl_checker import PDPLComplianceChecker
from .citc.citc_checker import CITCComplianceChecker
from .reports.report_generator import GRCReportGenerator

class GRC_Engine:
    """Manages and runs GRC compliance checks."""

    def __init__(self, config_path="config/grc_config.json"):
        """Initializes the GRC Engine with necessary checkers."""
        self.nca_checker = NCAComplianceChecker()
        self.pdpl_checker = PDPLComplianceChecker()
        self.citc_checker = CITCComplianceChecker()
        self.report_generator = GRCReportGenerator()
        self.results = {}

    def run_full_assessment(self, data_sources):
        """
        Runs a full GRC assessment across all frameworks.

        Args:
            data_sources (dict): A dictionary containing paths to data or connections
                                 to be assessed.

        Returns:
            dict: A dictionary containing the compliance results.
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

        Args:
            report_format (str): The format of the report (e.g., 'md', 'pdf', 'json').

        Returns:
            str: The path to the generated report.
        """
        if not self.results:
            print("No assessment has been run. Please run an assessment first.")
            return None

        print(f"Generating GRC report in {report_format} format...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"core/grc_engine/reports/GRC_Report_{timestamp}.{report_format}"

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
    # Example Usage
    engine = GRC_Engine()

    # Mock data sources for demonstration
    mock_data = {
        "system_logs": ["path/to/system.log"],
        "databases": ["postgresql://user:pass@host/db"],
        "network_traffic": ["path/to/traffic.pcap"]
    }

    # Run assessment
    assessment_results = engine.run_full_assessment(mock_data)

    # Generate report
    markdown_report = engine.generate_report(report_format="md")
    json_report = engine.generate_report(report_format="json")
