FROM python:3.12

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN python -m pip install poetry
RUN poetry config virtualenvs.create false

COPY . /app

RUN --mount=type=ssh mkdir -p ~/.ssh
RUN --mount=type=ssh ssh-keyscan github.com > ~/.ssh/known_hosts
RUN --mount=type=ssh poetry install --no-interaction

ENTRYPOINT [ "sh", "-c" ]
