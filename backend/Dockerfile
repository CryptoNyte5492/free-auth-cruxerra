# development backend image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps needed to build some Python packages & psycopg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential gcc gfortran libpq-dev libssl-dev libffi-dev pkg-config \
      && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy code (dev will typically use a volume to override this)
COPY backend /app

EXPOSE 8000

# Run migrations then dev server (dev mode). In production use gunicorn.
CMD ["bash", "-lc", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]