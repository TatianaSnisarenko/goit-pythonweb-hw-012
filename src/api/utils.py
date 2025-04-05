from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.schemas import HealthCheckResponse
from src.database.db import get_db

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
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify database connection.
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
