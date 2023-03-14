FROM python:3.10-slim AS pytorch-gpu

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch

FROM pytorch-gpu

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY serve.py .

CMD ["python", "serve.py"]
