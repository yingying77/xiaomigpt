FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv .venv && .venv/bin/pip install -r requirements.txt --no-cache-dir


FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /app/.env /app/.env
COPY xiaomibot/  ./xiaomibot/
COPY xiaogpt.py .

ENTRYPOINT [ "/app/.env/bin/pyton3", "xiaogpt.py" ]