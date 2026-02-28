#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Financial Intelligence Agent (وكيل الذكاء المالي)

Analyzes financial data, detects anomalies, generates reports, and provides
AI-powered insights - all processed locally with no data leaving the system.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Optional


class FinancialAgent:
    """
    AI-powered financial analysis agent.
    Connects to local Ollama LLM for intelligent insights.
    """

    AGENT_NAME = "وكيل الذكاء المالي"
    AGENT_VERSION = "3.0"

    def __init__(self, ollama_url: str = "http://ollama:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        print(f"✅ {self.AGENT_NAME} v{self.AGENT_VERSION} initialized.")

    def _ask_llm(self, prompt: str) -> str:
        """Sends a prompt to the local Ollama LLM and returns the response."""
        import requests
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "لا توجد استجابة من النموذج.")
        except Exception as e:
            return f"❌ خطأ في الاتصال بالنموذج المحلي: {e}"

    def analyze_financial_data(self, df: pd.DataFrame) -> dict:
        """
        Performs comprehensive financial analysis on a DataFrame.

        Args:
            df (pd.DataFrame): Financial data (e.g., transactions, P&L).

        Returns:
            dict: Analysis results including summary, anomalies, and AI insights.
        """
        print(f"📊 تحليل البيانات المالية: {len(df)} سجل...")

        # Basic statistical summary
        summary = df.describe(include='all').to_dict()

        # Anomaly detection (simple Z-score method)
        anomalies = []
        numeric_cols = df.select_dtypes(include='number').columns
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                z_scores = ((df[col] - mean) / std).abs()
                outliers = df[z_scores > 3]
                if not outliers.empty:
                    anomalies.append({
                        "column": col,
                        "count": len(outliers),
                        "description": f"تم اكتشاف {len(outliers)} قيمة شاذة في عمود '{col}'"
                    })

        # Prepare prompt for LLM
        data_summary_text = df.describe().to_string()
        prompt = f"""
أنت محلل مالي خبير. بناءً على ملخص البيانات المالية التالي، قدم تحليلاً موجزاً باللغة العربية يشمل:
1. أبرز الملاحظات
2. المخاطر المحتملة
3. التوصيات

ملخص البيانات:
{data_summary_text}

الشذوذات المكتشفة: {len(anomalies)} حالة

التحليل:
"""
        ai_insights = self._ask_llm(prompt)

        return {
            "agent": self.AGENT_NAME,
            "timestamp": datetime.now().isoformat(),
            "records_analyzed": len(df),
            "summary_statistics": summary,
            "anomalies_detected": anomalies,
            "ai_insights": ai_insights
        }

    def generate_report(self, analysis_result: dict, output_path: str = "financial_report.json") -> str:
        """Saves the analysis result to a JSON report file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
        print(f"✅ تم حفظ التقرير المالي: {output_path}")
        return output_path

    def detect_fraud(self, df: pd.DataFrame) -> list:
        """
        Basic fraud detection using rule-based heuristics.

        Args:
            df (pd.DataFrame): Transaction data.

        Returns:
            list: List of suspicious transaction records.
        """
        suspicious = []
        # Rule 1: Duplicate transactions (same amount, same date)
        if 'amount' in df.columns and 'date' in df.columns:
            duplicates = df[df.duplicated(subset=['amount', 'date'], keep=False)]
            if not duplicates.empty:
                suspicious.append({
                    "rule": "معاملات مكررة",
                    "count": len(duplicates),
                    "records": duplicates.to_dict('records')
                })

        # Rule 2: Round-number transactions (potential manipulation)
        if 'amount' in df.columns:
            round_numbers = df[df['amount'] % 1000 == 0]
            if len(round_numbers) > len(df) * 0.5:
                suspicious.append({
                    "rule": "نسبة عالية من المبالغ المستديرة",
                    "count": len(round_numbers),
                    "note": "قد يشير إلى تلاعب في البيانات"
                })

        return suspicious


if __name__ == '__main__':
    # Demo
    agent = FinancialAgent()
    sample_data = pd.DataFrame({
        'date': ['2025-01-01', '2025-01-01', '2025-01-02', '2025-01-03'],
        'amount': [5000, 5000, 150000, 200],
        'category': ['مشتريات', 'مشتريات', 'رواتب', 'مصاريف'],
        'description': ['فاتورة 1', 'فاتورة 1', 'رواتب يناير', 'قرطاسية']
    })
    result = agent.analyze_financial_data(sample_data)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
