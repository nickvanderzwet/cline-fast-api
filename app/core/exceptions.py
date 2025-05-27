"""Custom exceptions for the application."""

from fastapi import HTTPException


class DatabaseConnectionError(HTTPException):
    """Raised when database connection fails."""

    def __init__(self, detail: str = "Failed to connect to database"):
        super().__init__(status_code=500, detail=detail)


class TableNotFoundError(HTTPException):
    """Raised when a requested table is not found."""

    def __init__(self, table_name: str):
        super().__init__(
            status_code=404, detail=f"Table '{table_name}' not found or is excluded"
        )


class SchemaExtractionError(HTTPException):
    """Raised when schema extraction fails."""

    def __init__(self, detail: str = "Failed to extract database schema"):
        super().__init__(status_code=500, detail=detail)


class ModelGenerationError(HTTPException):
    """Raised when model generation fails."""

    def __init__(self, detail: str = "Failed to generate Pydantic models"):
        super().__init__(status_code=500, detail=detail)
