FROM python:3.14-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  UV_PYTHON_DOWNLOADS=never \
  UV_COMPILE_BYTECODE=1

WORKDIR /code
COPY pyproject.toml uv.lock /code/
RUN uv sync --locked --no-dev

COPY . /code
ENV PATH="/code/.venv/bin:$PATH"

# Single process only: the cache lives in app memory, so a second worker
# process would never see /update's data. gthread threads share it safely
# and keep one idle connection from blocking the whole app.
CMD ["gunicorn", "howhot.app:app", "-b", "0.0.0.0:8080", \
     "--worker-class", "gthread", "--threads", "4"]
