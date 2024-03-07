FROM python:3.10-slim

WORKDIR /app

RUN pip install poetry==1.8.1
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

COPY src /app

EXPOSE 3334

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3334"]
