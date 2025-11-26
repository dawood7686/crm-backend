# Use Python slim (adjust tag to your python version)
FROM python:3.11-slim

# OS deps (for psycopg2, Pillow, etc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create user
ENV APP_USER=app
RUN adduser --disabled-password --gecos "" $APP_USER
WORKDIR /app

# Copy requirements first for better caching
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Copy project
COPY . /app

# Make entrypoint executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use a non-root user
USER $APP_USER

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=crm.settings

# Default command is to run Django via gunicorn (overridden by docker-compose for worker/beat)
CMD ["/app/entrypoint.sh", "gunicorn", "crm.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--reload"]
