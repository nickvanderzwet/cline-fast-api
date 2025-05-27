"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import (
    add_health_endpoint,
    add_tables_info_endpoint,
    create_dynamic_endpoints,
)
from app.core.config import settings
from app.core.database import wait_for_db


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.title,
        description=settings.description,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET"],  # Only allow GET methods for read-only API
        allow_headers=["*"],
    )

    # Add health check endpoint
    add_health_endpoint(app)

    # Add tables info endpoint
    add_tables_info_endpoint(app)

    # Wait for database to be available before creating dynamic endpoints
    print("Waiting for database connection...")
    if wait_for_db(max_wait_time=60):
        try:
            create_dynamic_endpoints(app)
            print("Dynamic endpoints created successfully")
        except Exception as e:
            print(f"Error creating dynamic endpoints: {e}")
            # Continue without dynamic endpoints - health check will still work
    else:
        print("Database not available - starting without dynamic endpoints")

    return app


# Create the FastAPI app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
