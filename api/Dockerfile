FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install poetry and basic dependencies
RUN pip install --no-cache-dir six poetry==1.7.1 \
    && pip install --no-cache-dir langchain langchain-community langchain-core

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Debug: Check if files are copied
RUN ls -la

# Install dependencies with verbose output
RUN poetry config virtualenvs.create false \
    && POETRY_VIRTUALENVS_CREATE=false poetry install --no-interaction --no-ansi --no-root --verbose

# Copy application
COPY . .

# Debug: Verify langchain installation
RUN python -c "import langchain; print('Langchain version:', langchain.__version__)"

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]