# Dynamic Database API

A FastAPI application that automatically generates read-only REST API endpoints for database tables using Pydantic models. This project dynamically introspects your database schema and creates GET endpoints for each table.

## Features

- **Dynamic API Generation**: Automatically creates REST endpoints for all database tables
- **Pydantic Models**: Generates type-safe Pydantic models from database schema
- **MySQL Support**: Built-in support for MySQL databases
- **Docker Ready**: Complete Docker setup with MySQL database
- **Code Quality**: Integrated linting, formatting, and testing tools
- **Health Checks**: Built-in health check and table information endpoints
- **Configurable**: Environment-based configuration with sensible defaults

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd dynamic-database-api
```

2. Start the development environment:
```bash
make dev
```

This will:
- Install development dependencies
- Start Docker containers (API + MySQL)
- Set up the database with sample data

3. Access the API:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database configuration
```

3. Start your MySQL database and run:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

The application automatically generates the following endpoints for each table:

- `GET /tables` - List all available tables
- `GET /{table_name}` - Get all records from a table

### System Endpoints

- `GET /health` - Health check endpoint
- `GET /tables` - List all tables with their schemas

## Configuration

Configure the application using environment variables:

```bash
DB_HOST=localhost          # Database host
DB_PORT=3306              # Database port
DB_USER=root              # Database username
DB_PASSWORD=password      # Database password
DB_NAME=example           # Database name
EXCLUDED_TABLES=user      # Comma-separated list of tables to exclude
```

## Development

### Available Commands

```bash
make help           # Show all available commands
make install        # Install production dependencies
make install-dev    # Install development dependencies
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Run linting
make format         # Format code
make check          # Run all checks (lint + test)
make clean          # Clean up temporary files
make docker-up      # Start Docker containers
make docker-down    # Stop Docker containers
make docker-logs    # Show Docker logs
make run-local      # Run the application locally
```

### Code Quality

This project uses several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **Black**: Code formatter
- **MyPy**: Static type checker
- **Pre-commit**: Git hooks for code quality
- **Pytest**: Testing framework

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_specific.py
```

### Linting and Formatting

```bash
# Check code quality
make lint

# Format code
make format

# Run all checks
make check
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Dependency injection
│   │   └── endpoints.py        # Dynamic endpoint generation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database connection
│   │   └── exceptions.py      # Custom exceptions
│   ├── models/
│   │   └── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── model_generator.py  # Pydantic model generation
│       └── schema_extractor.py # Database schema extraction
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── init.sql               # Database initialization
├── requirements/
│   ├── base.txt              # Production dependencies
│   └── dev.txt               # Development dependencies
├── tests/
│   ├── __init__.py
│   └── conftest.py           # Test configuration
├── .env.example              # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml   # Pre-commit hooks
├── Makefile                  # Development commands
├── mypy.ini                  # MyPy configuration
├── pyproject.toml           # Project configuration
├── README.md
├── requirements.txt         # Main requirements file
└── ruff.toml               # Ruff configuration
```

## How It Works

1. **Schema Extraction**: The `SchemaExtractor` connects to your database and retrieves table schemas
2. **Model Generation**: The `ModelGenerator` creates Pydantic models from the database schema
3. **Endpoint Creation**: Dynamic read-only endpoints are generated for each table
4. **Type Safety**: All endpoints use the generated Pydantic models for request/response validation

## Database Support

Currently supports MySQL databases. The application automatically:
- Maps MySQL types to Python types
- Handles nullable fields
- Respects field constraints (length, defaults, etc.)
- Excludes specified tables from API generation

## Docker Setup

The Docker setup includes:
- **API Container**: FastAPI application with hot reload
- **MySQL Container**: MySQL 8.0 with sample data
- **Volume Persistence**: Database data persists between container restarts
- **Network Configuration**: Containers can communicate with each other

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting: `make check`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Port already in use**: If port 3306 is already in use, the Docker setup uses port 3307 for MySQL
2. **Database connection issues**: Check your environment variables and ensure the database is running
3. **Import errors**: Make sure all dependencies are installed: `make install-dev`

### Getting Help

- Check the logs: `make docker-logs`
- Run health check: `curl http://localhost:8000/health`
- View API documentation: http://localhost:8000/docs
