"""Dynamic API endpoint generation."""

from typing import TYPE_CHECKING, Any, cast

import mysql.connector
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_database_connection
from app.core.database import get_db_connection
from app.core.exceptions import DatabaseConnectionError
from app.services.model_generator import model_generator
from app.services.schema_extractor import SchemaExtractor

if TYPE_CHECKING:
    from mysql.connector.abstracts import MySQLConnectionAbstract
    from mysql.connector.pooling import PooledMySQLConnection


def create_dynamic_endpoints(app: FastAPI) -> None:
    """
    Create dynamic API endpoints for all database tables.

    Args:
        app: FastAPI application instance
    """
    try:
        # Generate models from database schema
        models = model_generator.generate_models_from_database()

        # Get table names
        with SchemaExtractor() as extractor:
            table_names = extractor.get_table_names()

        # Create endpoints for each table
        for table_name in table_names:
            if table_name in models:
                _create_table_endpoint(app, table_name, models[table_name])
            else:
                print(f"Warning: No model generated for table {table_name}")

    except Exception as e:
        print(f"Error creating dynamic endpoints: {e}")
        raise


def _create_table_endpoint(
    app: FastAPI, table_name: str, model_class: type[BaseModel]
) -> None:
    """
    Create a GET endpoint for a specific table.

    Args:
        app: FastAPI application instance
        table_name: Name of the database table
        model_class: Pydantic model class for the table
    """

    async def get_table_data(
        connection: "PooledMySQLConnection | MySQLConnectionAbstract" = Depends(
            get_database_connection
        ),
    ) -> list[dict[str, Any]]:
        """
        Get all data from the specified table.

        Returns:
            List of table records
        """
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {table_name}")
            results = cursor.fetchall()
            cursor.close()

            # Cast to handle MySQL connector's complex return types
            raw_results = cast(list[dict[str, Any]], results)

            # Validate data against the model
            validated_results = []
            for result in raw_results:
                try:
                    # Create model instance to validate data
                    validated_item = model_class(**result)
                    validated_results.append(validated_item.model_dump())
                except Exception as validation_error:
                    print(f"Validation error for {table_name}: {validation_error}")
                    # Include raw data if validation fails
                    validated_results.append(result)

            return validated_results

        except mysql.connector.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e

    # Set function metadata for better API documentation
    get_table_data.__name__ = f"get_{table_name}_data"
    get_table_data.__doc__ = f"Get all records from the {table_name} table"

    # Add the route to the app
    app.add_api_route(
        path=f"/{table_name}",
        endpoint=get_table_data,
        methods=["GET"],
        response_model=list[
            dict[str, Any]
        ],  # Use dict instead of model_class for type safety
        tags=[table_name],
        summary=f"Get all {table_name} records",
        description=f"Retrieve all records from the {table_name} table",
    )


def add_health_endpoint(app: FastAPI) -> None:
    """
    Add a health check endpoint.

    Args:
        app: FastAPI application instance
    """

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        try:
            # Test database connection
            connection = get_db_connection()
            if connection is None:
                raise DatabaseConnectionError()

            connection.ping(reconnect=True)
            connection.close()

            return {
                "status": "healthy",
                "database": "connected",
                "models_generated": len(model_generator.get_all_models()),
            }

        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Service unhealthy: {e}"
            ) from e


def add_tables_info_endpoint(app: FastAPI) -> None:
    """
    Add an endpoint to get information about available tables.

    Args:
        app: FastAPI application instance
    """

    @app.get("/tables", tags=["info"])
    async def get_tables_info() -> dict[str, Any]:
        """Get information about available tables and their models."""
        try:
            with SchemaExtractor() as extractor:
                table_names = extractor.get_table_names()

            models = model_generator.get_all_models()

            tables_info = []
            for table_name in table_names:
                table_info = {
                    "table_name": table_name,
                    "endpoint": f"/{table_name}",
                    "model_available": table_name in models,
                }

                if table_name in models:
                    model_class = models[table_name]
                    table_info["fields"] = list(model_class.model_fields.keys())

                tables_info.append(table_info)

            return {"total_tables": len(table_names), "tables": tables_info}

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error getting tables info: {e}"
            ) from e
