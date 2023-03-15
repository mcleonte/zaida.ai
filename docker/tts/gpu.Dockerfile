FROM python:3.10-slim AS pytorch-gpu

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch

FROM pytorch-gpu

WORKDIR /app

RUN pip install --no-cache-dir \
  mycroft-mimic3-tts \
  onnxruntime-gpu \
  websockets

COPY __main__.py app.py /usr/local/lib/python3.10/site-packages/mimic3_http/

ENTRYPOINT ["python", "-m", "mimic3_http", "--cuda"]
