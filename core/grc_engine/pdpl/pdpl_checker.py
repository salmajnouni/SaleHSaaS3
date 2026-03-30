#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDPL Compliance Checker

Checks for compliance with the Personal Data Protection Law (PDPL).
"""

import re

class PDPLComplianceChecker:
    """Scans data sources for PDPL compliance."""

    def __init__(self):
        """Initializes the checker with PDPL articles."""
        self.articles = {
            "Article-5": "Lawfulness of Processing",
            "Article-15": "Data Subject Rights",
            "Article-20": "Data Security",
        }
        self.findings = []
        # Patterns for Saudi National ID, Saudi Phone Numbers, Saudi IBAN, and CR
        self.patterns = {
            "National ID": re.compile(r"\b(1\d{9})\b"),
            "Phone Number": re.compile(r"\b(05\d{8})\b"),
            "Saudi IBAN": re.compile(r"\bSA\d{2}[A-Z0-9]{20}\b"),
            "Commercial Registration (CR)": re.compile(r"\b(1010\d{6})\b|\b(4030\d{6})\b")
        }

    def scan_text(self, text, source_name="Unknown Source"):
        """Scans text content for PDPL sensitive data."""
        local_findings = []
        for label, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                local_findings.append({
                    "control_id": "Article-20",
                    "description": f"Potential unencrypted {label} found in {source_name}.",
                    "matches_count": len(matches),
                    "severity": "Critical" if label in ["National ID", "Saudi IBAN"] else "High"
                })
        return local_findings

    def run_checks(self, database_connections):
        """
        Runs all PDPL checks against a list of database connections.
        Currently simulated for text scanning.
        """
        self.findings = []
        print(f"Running PDPL checks on {len(database_connections)} database(s)...")

        # Mock database scanning for now, but using the new scan_text logic
        for db_conn in database_connections:
            # In a real scenario, we would fetch data from the database here
            mock_data = "User data from DB contains ID 1234567890"
            res = self.scan_text(mock_data, source_name=db_conn)
            self.findings.extend(res)

        return {
            "framework": "Personal Data Protection Law (PDPL)",
            "status": "Incomplete" if self.findings else "Compliant",
            "findings": self.findings
        }
