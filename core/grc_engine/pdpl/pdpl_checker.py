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
        # Regex for Saudi National ID or phone numbers
        self.pii_pattern = re.compile(r"\b(1\d{9})\b|\b(05\d{8})\b")

    def scan_for_unencrypted_pii(self, db_connection_string):
        """
        Simulates scanning a database for unencrypted Personally Identifiable Information (PII).

        Args:
            db_connection_string (str): The connection string to the database.

        Returns:
            dict or None: A finding if unencrypted PII is detected.
        """
        # This is a mock scan. In a real implementation, we would connect to the DB,
        # query tables, and scan for patterns in the data.
        print(f"Simulating PII scan on: {db_connection_string}")
        mock_data_sample = "User John Doe, National ID 1234567890, phone 0501234567."

        if self.pii_pattern.search(mock_data_sample):
            return {
                "control_id": "Article-20",
                "description": "Potential unencrypted PII (National ID or Phone Number) found in database.",
                "severity": "Critical"
            }
        return None

    def run_checks(self, database_connections):
        """
        Runs all PDPL checks against a list of database connections.

        Args:
            database_connections (list): A list of database connection strings.

        Returns:
            dict: A dictionary of findings.
        """
        self.findings = []
        print(f"Running PDPL checks on {len(database_connections)} database(s)...")

        for db_conn in database_connections:
            finding = self.scan_for_unencrypted_pii(db_conn)
            if finding:
                self.findings.append(finding)

        return {
            "framework": "Personal Data Protection Law (PDPL)",
            "status": "Incomplete" if self.findings else "Compliant",
            "findings": self.findings
        }
