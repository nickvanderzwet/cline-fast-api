"""Database connection and utilities."""

import mysql.connector
from mysql.connector import Error
from typing import Optional
from app.core.config import settings


def get_db_connection() -> Optional[mysql.connector.MySQLConnection]:
    """
    Create and return a MySQL database connection.

    Returns:
        MySQL connection object or None if connection fails
    """
    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None


def test_db_connection() -> bool:
    """
    Test database connection.

    Returns:
        True if connection successful, False otherwise
    """
    connection = get_db_connection()
    if connection is None:
        return False

    try:
        connection.ping(reconnect=True)
        return True
    except Error:
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()
