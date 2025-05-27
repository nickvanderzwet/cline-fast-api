"""FastAPI dependencies."""

from fastapi import Depends, HTTPException
from app.core.database import get_db_connection, test_db_connection
from app.core.exceptions import DatabaseConnectionError


def get_database_connection():
    """
    FastAPI dependency to get database connection.

    Returns:
        Database connection

    Raises:
        DatabaseConnectionError: If connection fails
    """
    connection = get_db_connection()
    if connection is None:
        raise DatabaseConnectionError()

    try:
        yield connection
    finally:
        if connection and connection.is_connected():
            connection.close()


def verify_database_health():
    """
    FastAPI dependency to verify database health.

    Raises:
        DatabaseConnectionError: If database is not healthy
    """
    if not test_db_connection():
        raise DatabaseConnectionError("Database health check failed")
