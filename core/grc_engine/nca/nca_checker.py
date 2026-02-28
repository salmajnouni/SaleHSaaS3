#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NCA Compliance Checker

Checks for compliance with the National Cybersecurity Authority (NCA) Essential Cybersecurity Controls (ECC).
"""

import re

class NCAComplianceChecker:
    """Scans logs and configs for NCA ECC compliance."""

    def __init__(self):
        """Initializes the checker with NCA controls."""
        self.controls = {
            "ECC-1.1.1": "Password Complexity",
            "ECC-1.1.2": "Password History",
            "ECC-2.1.3": "Access Logging",
            "ECC-3.2.1": "Malware Defenses",
        }
        self.findings = []

    def check_password_complexity(self, log_content):
        """Checks for weak password indicators in logs."""
        # A very basic regex for demonstration purposes
        if re.search(r"password.*(is weak|is simple|too short)", log_content, re.IGNORECASE):
            return {"control_id": "ECC-1.1.1", "description": "Weak password detected in logs.", "severity": "High"}
        return None

    def check_access_logging(self, log_content):
        """Checks if access logs are being recorded."""
        if not re.search(r"(login successful|session opened|access granted)", log_content, re.IGNORECASE):
            return {"control_id": "ECC-2.1.3", "description": "No successful access logs found, logging may be disabled.", "severity": "Medium"}
        return None

    def run_checks(self, log_files):
        """
        Runs all NCA checks against a list of log files.

        Args:
            log_files (list): A list of paths to log files.

        Returns:
            dict: A dictionary of findings.
        """
        self.findings = []
        print(f"Running NCA checks on {len(log_files)} log file(s)...")

        for log_file in log_files:
            # In a real scenario, we would read the file content
            # For this example, we'll use mock content.
            mock_content = "user 'admin' login successful. user 'guest' password is weak."

            finding1 = self.check_password_complexity(mock_content)
            if finding1: self.findings.append(finding1)

            finding2 = self.check_access_logging(mock_content)
            if finding2: self.findings.append(finding2)

        return {
            "framework": "NCA Essential Cybersecurity Controls",
            "status": "Incomplete" if self.findings else "Compliant",
            "findings": self.findings
        }
