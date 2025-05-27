import os
import inspect
import asyncio
import uvicorn
import mysql.connector
from fastapi import FastAPI, Depends, HTTPException
from fastapi.routing import APIRoute
from typing import Any, Dict, List, Optional, Tuple, Type
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.absolute()))
from db_utils import get_db_connection
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_api_endpoints(app: FastAPI):
    """
    Creates GET API endpoints for each table in the database.
    """
    db_name = os.environ.get("DB_NAME")
    if not db_name:
        raise ValueError("DB_NAME environment variable not set")

    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Failed to connect to database")

    cursor = connection.cursor()
    cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{db_name}'")
    tables = [table[0] for table in cursor.fetchall()]

    for table_name in tables:
        @app.get(f"/{table_name}")
        async def get_table_data():
            connection = get_db_connection()
            if connection is None:
                raise HTTPException(status_code=500, detail="Failed to connect to database")
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {table_name}")
            results = cursor.fetchall()
            connection.close()
            return results
    connection.close()

create_api_endpoints(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
