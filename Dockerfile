FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv .venv && .venv/bin/pip install -r requirements.txt --no-cache-dir


FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY xiaomibot/  ./xiaomibot/
COPY xiaogpt.py .

ENTRYPOINT [ "/app/.venv/bin/python3", "xiaogpt.py" ]
