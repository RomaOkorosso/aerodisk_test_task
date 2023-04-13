# Установить базовый образ
FROM python:3.9-slim-buster

# Установить директорию приложения
WORKDIR /app

# Копировать файлы приложения и poetry.lock/pyproject.toml
COPY ./app /app
COPY poetry.lock pyproject.toml /app/

# Установить зависимости с помощью Poetry
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        curl \
        build-essential && \
    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && \
    /root/.poetry/bin/poetry install --no-dev && \
    apt-get remove -y --auto-remove curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Открыть порт из .env для трафика
ENV PORT=PORT
EXPOSE $PORT

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Запустить сервер с приложением
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80", "--reload"]
