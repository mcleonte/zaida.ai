
FROM python:alpine

WORKDIR /usr/src/app

RUN pip install --no-cache-dir websockets

COPY app.py .

CMD ["python", "./app.py"]

