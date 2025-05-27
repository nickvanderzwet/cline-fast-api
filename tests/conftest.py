"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    # This would be implemented with proper mocking
    # when actual tests are written
    pass
