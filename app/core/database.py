"""Database connection and utilities."""

import time

import mysql.connector
from mysql.connector import Error
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

from app.core.config import settings


def get_db_connection(
    max_retries: int = 5, retry_delay: int = 2
) -> PooledMySQLConnection | MySQLConnectionAbstract | None:
    """
    Create and return a MySQL database connection with retry logic.

    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retry attempts in seconds

    Returns:
        MySQL connection object or None if connection fails
    """
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name,
                connection_timeout=10,
                autocommit=True,
            )
            print(f"Successfully connected to database on attempt {attempt + 1}")
            return connection
        except Error as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")

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


def wait_for_db(max_wait_time: int = 60) -> bool:
    """
    Wait for database to become available.

    Args:
        max_wait_time: Maximum time to wait in seconds

    Returns:
        True if database becomes available, False if timeout
    """
    print("Waiting for database to become available...")
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        if test_db_connection():
            print("Database is now available!")
            return True

        print("Database not ready, waiting...")
        time.sleep(2)

    print(f"Database did not become available within {max_wait_time} seconds")
    return False
