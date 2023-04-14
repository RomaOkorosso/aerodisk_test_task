FROM python:3.10

WORKDIR /app

RUN apt update && apt install netcat postgresql-client dnsutils -y

RUN pip install --upgrade pip

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry config virtualenvs.create false --local
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false --local
RUN poetry update --no-dev

COPY . .

EXPOSE 8000

# Запустить сервер с приложением
#CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--reload"]
