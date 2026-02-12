FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Устанавливаем системные зависимости для сборки psycopg и cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set dependency environment location outside /app to survive volume mount
ENV UV_PROJECT_ENVIRONMENT="/venv"

# Create dependencies location
RUN uv venv /venv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимисти
RUN uv sync --frozen --no-dev --no-install-project

# Копируем код
COPY . .

# Устанавливаем сам проект
RUN uv sync --frozen --no-dev

# Добавляем venv в PATH
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH=/app/src

# Порт, который слушает приложение
EXPOSE 8000

# Команда по умолчанию (для Prod)
CMD ["sh", "-c", "alembic -c src/alembic.ini upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
