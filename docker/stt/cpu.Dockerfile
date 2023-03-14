FROM python:3.10-slim AS pytorch-cpu

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch \
        --extra-index-url https://download.pytorch.org/whl/cpu

FROM pytorch-cpu

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY serve.py .

CMD ["python", "serve.py"]
