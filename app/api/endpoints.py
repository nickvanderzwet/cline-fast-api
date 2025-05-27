"""Dynamic API endpoint generation."""

from typing import TYPE_CHECKING, Any, Type, cast

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


# Response models for API endpoints
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    database: str
    models_generated: int


class TableInfo(BaseModel):
    """Table information model."""

    table_name: str
    endpoint: str
    model_available: bool
    fields: list[str] | None = None


class TablesResponse(BaseModel):
    """Tables info response model."""

    total_tables: int
    tables: list[TableInfo]


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
    app: FastAPI, table_name: str, model_class: Type[BaseModel]
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
    ) -> list[BaseModel]:
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

            # Validate data against the model and return model instances
            validated_results = []
            for result in raw_results:
                try:
                    # Create model instance to validate data
                    validated_item = model_class(**result)
                    validated_results.append(validated_item)
                except Exception as validation_error:
                    print(f"Validation error for {table_name}: {validation_error}")
                    # For invalid data, create a simple BaseModel instance with the raw data
                    # This avoids the create_model type checking issues while maintaining functionality
                    class GenericModel(BaseModel):
                        class Config:
                            extra = "allow"
                    
                    validated_results.append(GenericModel(**result))

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
        response_model=list[model_class],  # type: ignore[valid-type]
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

    @app.get("/health", tags=["health"], response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        try:
            # Test database connection
            connection = get_db_connection()
            if connection is None:
                raise DatabaseConnectionError()

            connection.ping(reconnect=True)
            connection.close()

            return HealthResponse(
                status="healthy",
                database="connected",
                models_generated=len(model_generator.get_all_models()),
            )

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

    @app.get("/tables", tags=["info"], response_model=TablesResponse)
    async def get_tables_info() -> TablesResponse:
        """Get information about available tables and their models."""
        try:
            with SchemaExtractor() as extractor:
                table_names = extractor.get_table_names()

            models = model_generator.get_all_models()

            tables_info = []
            for table_name in table_names:
                model_available = table_name in models
                fields: list[str] | None = None

                if model_available:
                    model_class = models[table_name]
                    fields = list(model_class.model_fields.keys())

                table_info = TableInfo(
                    table_name=table_name,
                    endpoint=f"/{table_name}",
                    model_available=model_available,
                    fields=fields,
                )
                tables_info.append(table_info)

            return TablesResponse(total_tables=len(table_names), tables=tables_info)

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error getting tables info: {e}"
            ) from e
