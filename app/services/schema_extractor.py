"""Database schema extraction utilities."""

from typing import List, Dict, Any
import mysql.connector
from mysql.connector import Error
from app.core.database import get_db_connection
from app.core.config import settings
from app.core.exceptions import DatabaseConnectionError, SchemaExtractionError


class SchemaExtractor:
    """Extracts database schema information for model generation."""

    def __init__(self):
        self.connection = None

    def __enter__(self):
        self.connection = get_db_connection()
        if self.connection is None:
            raise DatabaseConnectionError()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_table_names(self) -> List[str]:
        """
        Get list of table names from the database, excluding configured tables.

        Returns:
            List of table names
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"SELECT table_name FROM information_schema.tables "
                f"WHERE table_schema = '{settings.db_name}'"
            )
            all_tables = [table[0] for table in cursor.fetchall()]

            # Filter out excluded tables
            excluded = settings.excluded_tables_list
            tables = [table for table in all_tables if table not in excluded]

            cursor.close()
            return tables

        except Error as e:
            raise SchemaExtractionError(f"Failed to get table names: {e}")

    def get_table_schema_ddl(self, table_name: str) -> str:
        """
        Get the CREATE TABLE statement for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            CREATE TABLE DDL statement
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            result = cursor.fetchone()
            cursor.close()

            if result:
                return result[1]  # The CREATE TABLE statement
            else:
                raise SchemaExtractionError(f"No schema found for table {table_name}")

        except Error as e:
            raise SchemaExtractionError(
                f"Failed to get schema for table {table_name}: {e}"
            )

    def get_all_schemas_ddl(self) -> str:
        """
        Get CREATE TABLE statements for all non-excluded tables.

        Returns:
            Combined DDL statements for all tables
        """
        tables = self.get_table_names()
        ddl_statements = []

        for table in tables:
            ddl = self.get_table_schema_ddl(table)
            ddl_statements.append(ddl)

        return "\n\n".join(ddl_statements)

    def get_table_columns_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get detailed column information for a table.

        Args:
            table_name: Name of the table

        Returns:
            List of column information dictionaries
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            cursor.close()
            return columns

        except Error as e:
            raise SchemaExtractionError(
                f"Failed to get columns for table {table_name}: {e}"
            )
