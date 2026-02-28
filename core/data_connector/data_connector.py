#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Universal Data Connector

Connects to any data source: SQL databases, ERP systems, files, and REST APIs.
All data is processed locally to ensure 100% privacy and sovereignty.
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Optional, Union

# --- SQL Connector ---
class SQLConnector:
    """Connects to SQL databases (PostgreSQL, MySQL, SQL Server, SQLite, Oracle)."""

    def __init__(self, connection_string: str):
        """
        Initializes the SQL connector.

        Args:
            connection_string (str): A SQLAlchemy-compatible connection string.
                Examples:
                - PostgreSQL: "postgresql://user:password@host:5432/dbname"
                - MySQL:      "mysql+pymysql://user:password@host:3306/dbname"
                - SQL Server: "mssql+pyodbc://user:password@host/dbname?driver=ODBC+Driver+17+for+SQL+Server"
                - SQLite:     "sqlite:///path/to/database.db"
        """
        self.connection_string = connection_string
        self.engine = None

    def connect(self):
        """Establishes the database connection."""
        try:
            from sqlalchemy import create_engine
            self.engine = create_engine(self.connection_string)
            print(f"✅ Connected to database successfully.")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def query(self, sql: str) -> Optional[pd.DataFrame]:
        """
        Executes a SQL query and returns results as a DataFrame.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            pd.DataFrame or None: The query results.
        """
        if not self.engine:
            print("Not connected. Call connect() first.")
            return None
        try:
            df = pd.read_sql(sql, self.engine)
            print(f"✅ Query returned {len(df)} rows.")
            return df
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None

    def list_tables(self) -> list:
        """Lists all tables in the connected database."""
        if not self.engine:
            return []
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        return inspector.get_table_names()


# --- File Connector ---
class FileConnector:
    """Reads and processes various file types: CSV, Excel, PDF, Word, JSON."""

    def read(self, file_path: str) -> Optional[Union[pd.DataFrame, str, dict]]:
        """
        Reads a file and returns its content in a usable format.

        Args:
            file_path (str): The path to the file.

        Returns:
            pd.DataFrame, str, or dict depending on the file type.
        """
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return None

        ext = path.suffix.lower()
        print(f"Reading {ext} file: {file_path}")

        try:
            if ext == ".csv":
                return pd.read_csv(file_path, encoding='utf-8-sig')
            elif ext in [".xlsx", ".xls"]:
                return pd.read_excel(file_path)
            elif ext == ".json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif ext == ".pdf":
                import pdfplumber
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                return text
            elif ext in [".docx", ".doc"]:
                from docx import Document
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            elif ext == ".txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print(f"⚠️ Unsupported file type: {ext}")
                return None
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None


# --- API Connector ---
class APIConnector:
    """Connects to REST APIs and retrieves data."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, headers: Optional[dict] = None):
        """
        Initializes the API connector.

        Args:
            base_url (str): The base URL of the API.
            api_key (str, optional): An API key for authentication.
            headers (dict, optional): Additional headers to include in requests.
        """
        import requests
        self.session = requests.Session()
        self.base_url = base_url.rstrip('/')

        self.session.headers.update({"Content-Type": "application/json"})
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        if headers:
            self.session.headers.update(headers)

    def get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Sends a GET request."""
        try:
            response = self.session.get(f"{self.base_url}/{endpoint.lstrip('/')}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API GET failed: {e}")
            return None

    def post(self, endpoint: str, data: dict) -> Optional[dict]:
        """Sends a POST request."""
        try:
            response = self.session.post(f"{self.base_url}/{endpoint.lstrip('/')}", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API POST failed: {e}")
            return None


# --- ERP Connector (SAP via REST API) ---
class ERPConnector:
    """Connects to ERP systems like SAP via OData or REST APIs."""

    def __init__(self, erp_type: str, base_url: str, username: str, password: str):
        """
        Initializes the ERP connector.

        Args:
            erp_type (str): The type of ERP (e.g., 'sap', 'oracle', 'dynamics').
            base_url (str): The base URL of the ERP system.
            username (str): The username for authentication.
            password (str): The password for authentication.
        """
        import requests
        self.erp_type = erp_type
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.base_url = base_url.rstrip('/')
        print(f"✅ ERP Connector initialized for {erp_type}.")

    def get_entity(self, entity_set: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        Retrieves an entity set from the ERP (e.g., a list of purchase orders).

        Args:
            entity_set (str): The name of the OData entity set (e.g., 'PurchaseOrderSet').
            params (dict, optional): OData query parameters (e.g., {'$top': 10, '$format': 'json'}).

        Returns:
            dict or None: The API response.
        """
        if params is None:
            params = {'$format': 'json'}
        try:
            url = f"{self.base_url}/{entity_set}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ ERP GET failed: {e}")
            return None


# --- Main Connector Factory ---
class DataConnector:
    """Factory class to create the appropriate connector based on the source type."""

    @staticmethod
    def connect(source_type: str, **kwargs):
        """
        Creates and returns the appropriate connector.

        Args:
            source_type (str): The type of data source.
                Options: 'sql', 'file', 'api', 'erp'
            **kwargs: Arguments specific to each connector type.

        Returns:
            An instance of the appropriate connector.
        """
        connectors = {
            "sql": SQLConnector,
            "file": FileConnector,
            "api": APIConnector,
            "erp": ERPConnector,
        }
        connector_class = connectors.get(source_type.lower())
        if not connector_class:
            raise ValueError(f"Unknown source type: '{source_type}'. Choose from {list(connectors.keys())}")

        print(f"✅ Creating {source_type.upper()} connector...")
        return connector_class(**kwargs)


if __name__ == '__main__':
    print("=== SaleHSaaS Data Connector Demo ===\n")

    # Example 1: SQL
    print("--- SQL Connector ---")
    sql_conn = DataConnector.connect("sql", connection_string="sqlite:///test.db")
    sql_conn.connect()

    # Example 2: File
    print("\n--- File Connector ---")
    file_conn = DataConnector.connect("file")
    # df = file_conn.read("path/to/data.xlsx")

    # Example 3: API
    print("\n--- API Connector ---")
    api_conn = DataConnector.connect("api", base_url="https://jsonplaceholder.typicode.com")
    result = api_conn.get("/todos/1")
    print(f"API Result: {result}")
