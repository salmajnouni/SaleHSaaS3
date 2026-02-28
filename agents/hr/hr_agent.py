#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Human Resources Agent (وكيل الموارد البشرية)

Manages employee data, analyzes HR metrics, ensures Saudi Labor Law compliance,
and generates HR reports - all processed locally.
"""

import json
import pandas as pd
from datetime import datetime, date
from typing import Optional


class HRAgent:
    """
    AI-powered HR management agent compliant with Saudi Labor Law.
    """

    AGENT_NAME = "وكيل الموارد البشرية"
    AGENT_VERSION = "3.0"

    # Saudi Labor Law key thresholds
    LABOR_LAW = {
        "max_working_hours_per_week": 48,
        "max_working_hours_ramadan": 36,
        "annual_leave_days_under_5_years": 21,
        "annual_leave_days_over_5_years": 30,
        "end_of_service_rate_under_5_years": 0.5,  # half month per year
        "end_of_service_rate_over_5_years": 1.0,   # full month per year
        "notice_period_days": 60,
        "probation_max_months": 3,
        "saudization_rates": {
            "large": 0.75,  # 75% for large companies
            "medium": 0.50,
            "small": 0.35
        }
    }

    def __init__(self, ollama_url: str = "http://ollama:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        print(f"✅ {self.AGENT_NAME} v{self.AGENT_VERSION} initialized.")

    def calculate_end_of_service(self, monthly_salary: float, years_of_service: float) -> dict:
        """
        Calculates end-of-service gratuity per Saudi Labor Law.

        Args:
            monthly_salary (float): Last monthly salary in SAR.
            years_of_service (float): Total years of service.

        Returns:
            dict: Calculation breakdown and total amount.
        """
        if years_of_service < 2:
            return {
                "eligible": False,
                "reason": "لا يستحق مكافأة نهاية الخدمة (أقل من سنتين)",
                "amount": 0
            }

        amount = 0
        breakdown = []

        # First 5 years: half month per year
        first_period = min(years_of_service, 5)
        first_amount = monthly_salary * self.LABOR_LAW["end_of_service_rate_under_5_years"] * first_period
        breakdown.append(f"السنوات الأولى ({first_period:.1f} سنة × نصف راتب): {first_amount:,.2f} ريال")
        amount += first_amount

        # After 5 years: full month per year
        if years_of_service > 5:
            remaining = years_of_service - 5
            remaining_amount = monthly_salary * self.LABOR_LAW["end_of_service_rate_over_5_years"] * remaining
            breakdown.append(f"السنوات بعد الخامسة ({remaining:.1f} سنة × راتب كامل): {remaining_amount:,.2f} ريال")
            amount += remaining_amount

        return {
            "eligible": True,
            "monthly_salary": monthly_salary,
            "years_of_service": years_of_service,
            "total_amount": round(amount, 2),
            "breakdown": breakdown,
            "legal_basis": "نظام العمل السعودي - المادة 84"
        }

    def check_saudization(self, total_employees: int, saudi_employees: int, company_size: str = "medium") -> dict:
        """
        Checks Saudization (Nitaqat) compliance.

        Args:
            total_employees (int): Total number of employees.
            saudi_employees (int): Number of Saudi employees.
            company_size (str): Company size ('large', 'medium', 'small').

        Returns:
            dict: Saudization compliance status.
        """
        if total_employees == 0:
            return {"error": "لا يوجد موظفون"}

        current_rate = saudi_employees / total_employees
        required_rate = self.LABOR_LAW["saudization_rates"].get(company_size, 0.50)
        gap = required_rate - current_rate
        required_additional = max(0, round(gap * total_employees))

        status = "ممتثل ✅" if current_rate >= required_rate else "غير ممتثل ❌"
        nitaqat_band = "أخضر" if current_rate >= required_rate else ("أصفر" if gap < 0.1 else "أحمر")

        return {
            "total_employees": total_employees,
            "saudi_employees": saudi_employees,
            "current_saudization_rate": f"{current_rate:.1%}",
            "required_rate": f"{required_rate:.1%}",
            "compliance_status": status,
            "nitaqat_band": nitaqat_band,
            "additional_saudis_needed": required_additional,
            "company_size": company_size
        }

    def analyze_hr_data(self, df: pd.DataFrame) -> dict:
        """
        Analyzes HR data for key metrics and compliance.

        Args:
            df (pd.DataFrame): Employee data DataFrame.

        Returns:
            dict: HR analytics results.
        """
        print(f"👥 تحليل بيانات الموارد البشرية: {len(df)} موظف...")

        metrics = {
            "total_employees": len(df),
            "timestamp": datetime.now().isoformat()
        }

        if 'nationality' in df.columns:
            nationality_counts = df['nationality'].value_counts().to_dict()
            saudi_count = nationality_counts.get('سعودي', nationality_counts.get('Saudi', 0))
            metrics['nationality_breakdown'] = nationality_counts
            metrics['saudization_rate'] = f"{(saudi_count / len(df)):.1%}"

        if 'department' in df.columns:
            metrics['department_distribution'] = df['department'].value_counts().to_dict()

        if 'salary' in df.columns:
            metrics['salary_stats'] = {
                "average": round(df['salary'].mean(), 2),
                "median": round(df['salary'].median(), 2),
                "min": df['salary'].min(),
                "max": df['salary'].max()
            }

        if 'gender' in df.columns:
            metrics['gender_distribution'] = df['gender'].value_counts().to_dict()

        return metrics

    def generate_hr_report(self, metrics: dict, output_path: str = "hr_report.json") -> str:
        """Saves HR metrics to a JSON report."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2, default=str)
        print(f"✅ تم حفظ تقرير الموارد البشرية: {output_path}")
        return output_path


if __name__ == '__main__':
    agent = HRAgent()

    # Test end of service calculation
    eos = agent.calculate_end_of_service(monthly_salary=10000, years_of_service=7.5)
    print("مكافأة نهاية الخدمة:")
    print(json.dumps(eos, ensure_ascii=False, indent=2))

    # Test Saudization
    saudization = agent.check_saudization(total_employees=100, saudi_employees=45, company_size="medium")
    print("\nالسعودة:")
    print(json.dumps(saudization, ensure_ascii=False, indent=2))
