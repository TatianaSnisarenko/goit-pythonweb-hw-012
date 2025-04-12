from fastapi import FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.api import contacts, utils, auth, users
from slowapi.errors import RateLimitExceeded

"""
Main application module.

This module initializes the FastAPI application, configures middleware, 
includes API routers, and defines global exception handlers. It also provides 
the entry point for running the application.

Routes:
    /api: Prefix for all API routes, including utilities, contacts, authentication, and users.

Middleware:
    CORSMiddleware: Enables Cross-Origin Resource Sharing (CORS) for specified origins.

Exception Handlers:
    RateLimitExceeded: Handles rate-limiting errors.
    HTTPException: Handles general HTTP exceptions.

Entry Point:
    Runs the application using Uvicorn.
"""

app = FastAPI()

origins = [
    "<http://localhost:8000>",
    "<http://localhost:8080>",
    "<https://contacts-api-2npo.onrender.com>",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(utils.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handles rate-limiting errors.

    Args:
        request (Request): The incoming HTTP request.
        exc (RateLimitExceeded): The exception raised when the rate limit is exceeded.

    Returns:
        JSONResponse: A JSON response with a 429 status code and an error message.
    """
    return JSONResponse(
        status_code=429,
        content={"error": "Exceeded limit of requests. Please, try again later"},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handles general HTTP exceptions.

    Args:
        request (Request): The incoming HTTP request.
        exc (HTTPException): The exception raised during request processing.

    Returns:
        JSONResponse: A JSON response with the exception's status code and detail message.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",  # The application to run
        host="127.0.0.1",  # The host address
        port=8000,  # The port number
        reload=True,  # Enable auto-reload for development
    )
