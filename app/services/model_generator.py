"""Pydantic model generation using database schema introspection."""

import re
from typing import Any, cast

from pydantic import BaseModel, Field, create_model

from app.core.exceptions import ModelGenerationError
from app.services.schema_extractor import SchemaExtractor


class ModelGenerator:
    """Generates Pydantic models from database schema using direct introspection."""

    def __init__(self) -> None:
        self.generated_models: dict[str, type[BaseModel]] = {}

    def generate_models_from_database(self) -> dict[str, type[BaseModel]]:
        """
        Generate Pydantic models directly from database schema.

        Returns:
            Dictionary mapping table names to Pydantic model classes
        """
        try:
            with SchemaExtractor() as extractor:
                table_names = extractor.get_table_names()

                models = {}
                for table_name in table_names:
                    columns_info = extractor.get_table_columns_info(table_name)
                    model_class = self._create_pydantic_model(table_name, columns_info)
                    models[table_name] = model_class

                self.generated_models.update(models)
                return models

        except Exception as e:
            raise ModelGenerationError(
                f"Failed to generate models from database: {e}"
            ) from e

    def _create_pydantic_model(
        self, table_name: str, columns_info: list[dict[str, Any]]
    ) -> type[BaseModel]:
        """
        Create a Pydantic model from table column information.

        Args:
            table_name: Name of the table
            columns_info: List of column information dictionaries

        Returns:
            Pydantic model class
        """
        try:
            fields: dict[str, Any] = {}

            for column in columns_info:
                field_name = str(column["Field"])
                field_type = str(column["Type"])
                is_nullable = str(column["Null"]) == "YES"
                default_value = column["Default"]

                # Map MySQL types to Python types
                python_type = self._map_mysql_type_to_python(field_type, is_nullable)

                # Create field with constraints
                field_info = self._create_field_info(
                    column, python_type, is_nullable, default_value
                )
                fields[field_name] = field_info

            # Create the model class name (PascalCase)
            model_name = self._table_name_to_class_name(table_name)

            # Create the Pydantic model with proper type casting
            model_class = create_model(model_name, **fields)
            return cast(type[BaseModel], model_class)

        except Exception as e:
            raise ModelGenerationError(
                f"Failed to create model for table {table_name}: {e}"
            ) from e

    def _map_mysql_type_to_python(
        self, mysql_type: str, is_nullable: bool
    ) -> type[Any]:
        """
        Map MySQL column type to Python type.

        Args:
            mysql_type: MySQL column type string
            is_nullable: Whether the column is nullable

        Returns:
            Python type
        """
        mysql_type_lower = mysql_type.lower()

        # Integer types
        if any(
            t in mysql_type_lower
            for t in ["int", "integer", "bigint", "smallint", "tinyint"]
        ):
            # Special case for tinyint(1) which is often used as boolean
            if "tinyint(1)" in mysql_type_lower:
                base_type: type[Any] = bool
            else:
                base_type = int
        # Float types
        elif any(
            t in mysql_type_lower for t in ["float", "double", "decimal", "numeric"]
        ):
            base_type = float
        # String types
        elif any(
            t in mysql_type_lower
            for t in ["varchar", "char", "text", "longtext", "mediumtext", "tinytext"]
        ):
            base_type = str
        # Date/time types
        elif any(
            t in mysql_type_lower for t in ["date", "time", "datetime", "timestamp"]
        ):
            base_type = str  # We'll handle these as strings for simplicity
        # Boolean type
        elif "boolean" in mysql_type_lower:
            base_type = bool
        # JSON type
        elif "json" in mysql_type_lower:
            base_type = dict
        # Binary types
        elif any(t in mysql_type_lower for t in ["blob", "binary", "varbinary"]):
            base_type = bytes
        # Default to string for unknown types
        else:
            base_type = str

        # Make optional if nullable - use proper type annotation
        if is_nullable:
            # Return the union type properly for mypy
            return type(
                base_type.__name__ + " | None", (object,), {"__origin__": base_type}
            )
        return base_type

    def _create_field_info(
        self,
        column: dict[str, Any],
        python_type: type[Any],
        is_nullable: bool,
        default_value: Any,
    ) -> tuple[type[Any], Any]:
        """
        Create field information for Pydantic model.

        Args:
            column: Column information dictionary
            python_type: Python type for the field
            is_nullable: Whether the field is nullable
            default_value: Default value for the field

        Returns:
            Tuple of (type, Field) for Pydantic model creation
        """
        field_kwargs: dict[str, Any] = {}

        # Add description
        field_kwargs["description"] = f"Column: {column['Field']} ({column['Type']})"

        # Handle default values
        if default_value is not None and default_value != "NULL":
            # Try to convert default value to appropriate type
            try:
                if python_type == int or (
                    hasattr(python_type, "__origin__")
                    and python_type.__args__[0] == int
                ):
                    converted_default: Any = int(default_value)
                elif python_type == float or (
                    hasattr(python_type, "__origin__")
                    and python_type.__args__[0] == float
                ):
                    converted_default = float(default_value)
                elif python_type == bool or (
                    hasattr(python_type, "__origin__")
                    and python_type.__args__[0] == bool
                ):
                    converted_default = bool(int(default_value))
                else:
                    converted_default = str(default_value)
                field_kwargs["default"] = converted_default
            except (ValueError, TypeError):
                # If conversion fails, use string representation
                field_kwargs["default"] = str(default_value)
        elif is_nullable:
            field_kwargs["default"] = None

        # Add constraints based on column type
        if "varchar" in str(column["Type"]).lower():
            # Extract length from varchar(n)
            try:
                match = re.search(r"varchar\((\d+)\)", str(column["Type"]).lower())
                if match:
                    max_length = int(match.group(1))
                    field_kwargs["max_length"] = max_length
            except Exception:
                pass

        return (python_type, Field(**field_kwargs))

    def _table_name_to_class_name(self, table_name: str) -> str:
        """
        Convert snake_case table name to PascalCase class name.

        Args:
            table_name: snake_case table name

        Returns:
            PascalCase class name
        """
        return "".join(word.capitalize() for word in table_name.split("_"))

    def get_model_for_table(self, table_name: str) -> type[BaseModel]:
        """
        Get the Pydantic model for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            Pydantic model class for the table
        """
        if table_name not in self.generated_models:
            raise ModelGenerationError(f"No model found for table: {table_name}")

        return self.generated_models[table_name]

    def get_all_models(self) -> dict[str, type[BaseModel]]:
        """
        Get all generated models.

        Returns:
            Dictionary mapping table names to Pydantic model classes
        """
        return self.generated_models.copy()


# Global model generator instance
model_generator = ModelGenerator()
