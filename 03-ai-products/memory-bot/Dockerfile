FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py db.py llm_proxy.py ./

ENV PYTHONUNBUFFERED=1
ENV SQLITE_PATH=/app/data/bot.db

CMD ["python", "-u", "main.py"]
