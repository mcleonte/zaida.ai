"""
Speech to text websocket server module
"""

import logging
import asyncio
import socketio
import os
import requests
import json

import websockets
import numpy as np
import torch
import whisper

PROXY_PORT = os.environ["PROXY_PORT"]
NLU_HOST = os.environ["NLU_HOST"]
NLU_PORT = os.environ["NLU_PORT"]
NLU_URI = f"http://{NLU_HOST}:{NLU_PORT}/socket.io"
# NLU_URI = f"http://{NLU_HOST}:{NLU_PORT}/webhooks/rest/webhook"

MODEL_NAME = os.environ["MODEL_NAME"] or "small.en"
MODEL_PATH = os.environ["MODEL_PATH"] or "/app/models/"
FP16 = torch.cuda.is_available()

logger = logging.getLogger("zaida.stt")
logger.setLevel(os.environ["LOG_LEVEL"])
logger.addHandler(logging.StreamHandler())

logger.info("Loading model '%s'", MODEL_NAME)
model = whisper.load_model(MODEL_NAME, download_root=MODEL_PATH)
logger.info("Model loaded.")

queue = asyncio.Queue()


def transcribe(audio):
  logger.info("Received audio chunk of size %s", len(audio))
  audio = np.frombuffer(audio, np.int16).flatten().astype(np.float32) / 32768.0
  result = model.transcribe(audio, fp16=FP16)
  logger.info("Result: '%s'", result)
  for i, segment in enumerate(result["segments"]):
    logger.info("Segment %s: '%s'", i, segment)
  return result["text"]


async def serve_forever():

  async def serve(websocket):
    async for audio in websocket:
      queue.put_nowait(transcribe(audio))

  async with websockets.serve(serve, "0.0.0.0", PROXY_PORT, logger=logger):
    await asyncio.Future()


async def send_forever():
  sio = socketio.AsyncClient(logger=True)

  @sio.event
  async def connect():
    logger.info("STT Connected to NLU")

  await sio.connect(NLU_URI)
  while True:
    await sio.emit(
        "message",
        {
            "sender": "zaida-stt",
            "message": await queue.get(),
            # "metadata": json.dumps({})
        },
    )


# async def send_forever():
#   async with websockets.connect(NLU_URI, logger=logger) as websocket:
#     while True:
#       await websocket.send(await queue.get())
#     # requests.post(
#     #     NLU_URI,
#     #     data=json.dumps({"message": result["text"]}),
#     #     stream=True,
#     #     timeout=None,
#     # )


async def main():
  await asyncio.gather(
      serve_forever(),
      send_forever(),
  )


asyncio.run(main())
