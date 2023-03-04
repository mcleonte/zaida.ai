FROM python:3.10

WORKDIR /app/

COPY requirements.txt serve.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "serve.py"]
