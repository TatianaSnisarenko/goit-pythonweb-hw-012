#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z postgres 5432; do
  sleep 0.1
done

echo "PostgreSQL started"
alembic upgrade head
exec uvicorn main:app --host 0.0.0.0 --port 8000