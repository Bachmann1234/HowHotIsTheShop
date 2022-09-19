FROM python:3.10.7-slim-bullseye

ARG HOW_HOT_ENV

ENV HOW_HOT_ENV=${HOW_HOT_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.2.1

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$HOW_HOT_ENV" == production && echo "--no-dev") --no-interaction --no-ansi

COPY . /code

CMD ["gunicorn", "howhot.app:app", "-b", "0.0.0.0:8080"]
