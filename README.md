# Contacts API

Contacts API is a RESTful API for managing contacts for each user separately using an authentication mechanism. It provides functionality to create, read, update, and delete contacts, as well as search for contacts and retrieve a list of contacts with upcoming birthdays. Additionally, users can view their profile information and update their avatar. The application includes an email verification feature that sends a confirmation email to users upon registration. This ensures that only valid email addresses are used for account creation.

## Features

### Core Functionality:

1. **CRUD Operations**:

   - User Registration with email verifiation
   - User Login
   - Create a new contact.
   - Retrieve a list of contacts with pagination.
   - Retrieve a single contact by its ID.
   - Update an existing contact by its ID.
   - Delete a contact by its ID.
   - View personal profile information.
   - Update profile avatar.

2. **Search Contacts**:

   - Search by first name, last name, or email with pagination.

3. **Upcoming Birthdays**:
   - Retrieve a list of contacts with birthdays in the next `n` days (default: 7 days) with pagination.

## Prerequisites

- Python 3.10+
- Docker
- Email account with allowed smtp
- Account in Cloudinary for working with sdk

## Setup and Usage

## Local setup

### Step 1: Start a PostgreSQL Container

Run the following command (replace all values in `{}`) to start a PostgreSQL container:

```sh
docker run --name {container_name} -p {postgres_port}:5432 -e POSTGRES_USER={postgres_user} -e POSTGRES_PASSWORD={postgres_password} -d postgres
```

Create a database with the name `contact_db`:

```sh
docker exec -it {container_name} psql -U {postgres_user}
CREATE DATABASE {db_name};
exit;
```

### Step 2: Create a `.env` file and configure the following values:

```env
POSTGRES_DB={db_name}
POSTGRES_USER={postgres_user}
POSTGRES_PASSWORD={postgres_password}
POSTGRES_PORT={postgres_port}
POSTGRES_HOST={postgres_host}

DB_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600

MAIL_USERNAME={email_address}
MAIL_PASSWORD={email_password}
MAIL_FROM={email_address}
MAIL_PORT={port}
MAIL_SERVER={smrp_server}
MAIL_FROM_NAME=Contacts API Service
MAIL_STARTTLS=False
MAIL_SSL_TLS=True
USE_CREDENTIALS=True
VALIDATE_CERTS=True

CLOUDINARY_NAME={cloud_name}
CLOUDINARY_API_KEY={api_key}
CLOUDINARY_API_SECRET={api_secret}
```

For POSTGRES_HOST use localhost for local run and postgres for container run

Ensure that the email account you use has SMTP enabled.

### Step 3: Install Dependencies

Ensure you have a virtual environment activated, then install dependencies:

```sh
pip install -r requirements.txt
```

### Step 4: Configure and Apply Migrations

Use Alembic to manage database migrations. To create and apply the initial migration, run:

```sh
alembic init migrations
```

#### Configure `env.py`

Replace the beginning of the `migrations/env.py` file with the following code:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context

from src.database.models import Base
from src.conf.config import config as app_config
```

Find the following line in `env.py`:

```python
target_metadata = None
```

Replace `None` with:

```python
target_metadata = Base.metadata
```

Replace the database connection string with the actual connection:

```python
config.set_main_option("sqlalchemy.url", app_config.DB_URL)
```

Modify the `run_migrations_online` function for asynchronous migrations:

```python
def run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())
```

Apply the migrations:

```sh
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Step 5: Run the Application

Start the FastAPI server:

```sh
fastapi dev src/main.py
```

### Running using docker-compose ise command

```sh
docker-compose up --build
```

### Use Swagger for API Exploration

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Start application using docker-compose

### Step 1: Create a `.env` file and configure the following values:

```env
POSTGRES_DB={db_name}
POSTGRES_USER={postgres_user}
POSTGRES_PASSWORD={postgres_password}
POSTGRES_PORT={postgres_port}
POSTGRES_HOST={postgres_host}

DB_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600

MAIL_USERNAME={email_address}
MAIL_PASSWORD={email_password}
MAIL_FROM={email_address}
MAIL_PORT={port}
MAIL_SERVER={smrp_server}
MAIL_FROM_NAME=Contacts API Service
MAIL_STARTTLS=False
MAIL_SSL_TLS=True
USE_CREDENTIALS=True
VALIDATE_CERTS=True

CLOUDINARY_NAME={cloud_name}
CLOUDINARY_API_KEY={api_key}
CLOUDINARY_API_SECRET={api_secret}
```

For POSTGRES_HOST use localhost for local run and postgres for container run

Ensure that the email account you use has SMTP enabled.

### Step 2: Start the application

First start up:

```sh
docker-compose up --build
```

Following start ups:

```sh
docker-compose up -d
```

### Use Swagger for API Exploration

- Swagger UI: [http://localhost:8080/docs](http://localhost:8080/docs)
- ReDoc: [http://localhost:8080/redoc](http://localhost:8080/redoc)
