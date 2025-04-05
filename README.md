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
ACCESS_TOKEN_EXPIRATION_SECONDS=3600
REFRESH_TOKEN_EXPIRATION_SECONDS=604800

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

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}
```

For POSTGRES_HOST use localhost for local run and postgres for container run

Ensure that the email account you use has SMTP enabled.

### Step 3: Install Dependencies

Ensure you have a virtual environment activated, then install dependencies:

```sh
pip install -r requirements.txt
```

### Step 4: Apply Migrations

Use Alembic to apply database migrations:

Apply the migrations:

```sh
alembic upgrade head
```

### Step 5: Start Redis

```sh
docker run --name {container_name} -d -p {redis_port}:6379 redis
```

### Step 5: Run the Application

Start the FastAPI server:

```sh
fastapi dev main.py
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
ACCESS_TOKEN_EXPIRATION_SECONDS=3600
REFRESH_TOKEN_EXPIRATION_SECONDS=604800

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


REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}
```

For POSTGRES_HOST use localhost for local run and postgres for container run
For REDIS_HOST use localhost for local run and redis for container run

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
