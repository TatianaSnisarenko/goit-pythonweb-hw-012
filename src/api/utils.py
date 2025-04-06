from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.schemas import HealthCheckResponse
from src.database.db import get_db

"""
Utils API module.

This module provides utility endpoints for the application. It includes functionality 
for performing health checks to verify the database connection and ensure the API is operational.

Routes:
    /utils/healthchecker:
        - GET: Perform a health check to verify the database connection.

Dependencies:
    - Database session (`AsyncSession`) is used for executing database queries.

Exception Handling:
    - Raises `HTTPException` if the database connection fails or is not configured correctly.
"""

router = APIRouter(tags=["utils"])


@router.get(
    "/healthchecker",
    response_model=HealthCheckResponse,
    responses={
        200: {
            "description": "Successful health check",
            "content": {
                "application/json": {"example": {"message": "Welcome to ContactAPI!"}}
            },
        },
        500: {
            "description": "Database connection error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error connecting to the database"}
                }
            },
        },
    },
)
async def healthchecker(db: AsyncSession = Depends(get_db)) -> HealthCheckResponse:
    """
    Health check endpoint to verify database connection.

    This endpoint checks the connection to the database by executing a simple query.
    If the database is reachable and configured correctly, it returns a success message.
    Otherwise, it raises an HTTP exception.

    Args:
        db (AsyncSession): The database session dependency.

    Returns:
        HealthCheckResponse: A success message indicating the API is healthy.

    Raises:
        HTTPException: If the database connection fails or is not configured correctly.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to ContactAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )
