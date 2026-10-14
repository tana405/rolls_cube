FROM python:3.10-slim

RUN useradd python -s /bin/false

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]


