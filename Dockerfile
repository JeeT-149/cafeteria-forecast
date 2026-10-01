FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest fastapi uvicorn

COPY . .

CMD ["python", "-c", "print('Ready')"]
