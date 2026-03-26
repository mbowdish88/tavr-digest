FROM python:3.12-slim

WORKDIR /app

COPY requirements-bot.txt .
RUN pip install --no-cache-dir -r requirements-bot.txt

COPY bot_server.py .

CMD ["python", "bot_server.py"]
