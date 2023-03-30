"""
Speech to text websocket server module
"""

import os
import logging
import asyncio
import requests
import json

import websockets
import numpy as np
import torch
import whisper

STT_PORT = os.environ["STT_PORT"]
NLU_URI = os.environ["NLU_URI"]

MODEL_NAME = os.environ["MODEL_NAME"] or "small.en"
MODEL_PATH = os.environ["MODEL_PATH"] or "/app/models/"

FP16 = torch.cuda.is_available()
DEVICE = "cuda" if FP16 else "cpu"

logging.basicConfig(format="%(asctime)s | %(message)s")
logger = logging.getLogger("zaida.stt")
logger.setLevel(os.environ["LOG_LEVEL"])
logger.addHandler(logging.StreamHandler())

logger.info("Loading model '%s'", MODEL_NAME)
model = whisper.load_model(MODEL_NAME, download_root=MODEL_PATH).to(DEVICE)
logger.info("Model loaded.")


def transcribe(audio):
  logger.info("Received audio chunk of size %s", len(audio))
  audio = np.frombuffer(audio, np.int16).flatten().astype(np.float32) / 32768.0
  result = model.transcribe(audio, fp16=FP16)
  logger.info("Result: '%s'", result)
  for i, segment in enumerate(result["segments"]):
    logger.info("Segment %s: '%s'", i, segment)
  return result


def send(text: str):
  logger.debug("Sending text to %s: %s", NLU_URI, text)
  requests.post(
      NLU_URI,
      json.dumps({
          "message": text,
          "sender": os.environ["ZAIDA_USER"],
      }),
      stream=True,
      timeout=None,
  )


async def serve(websocket):
  async for audio in websocket:
    send(transcribe(audio)["text"])


async def main():
  async with websockets.serve(serve, "0.0.0.0", STT_PORT, logger=logger):
    await asyncio.Future()


asyncio.run(main())
