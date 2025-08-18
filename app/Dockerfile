    FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libmariadb-dev pkg-config && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Poetry and dependencies
COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Copy application code (not mounted in prod, so we copy everything)
COPY ./src ./src
COPY ./templates ./templates
COPY ./static ./static

EXPOSE 8000

# No --reload in prod
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
