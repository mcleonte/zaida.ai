"""
Speech to text websocket server module
"""

import os
import logging
import asyncio

import websockets
import numpy as np
import torch
import whisper

MODEL_NAME = os.environ["MODEL_NAME"] or "small.en"
MODEL_PATH = os.environ["MODEL_PATH"] or "/app/models/"

FP16 = torch.cuda.is_available()
DEVICE = "cuda" if FP16 else "cpu"

logging.basicConfig(
    format="%(asctime)s | %(message)s",
    level=os.environ.get("LOG_LEVEL"),
)
logger = logging.getLogger("zaida.stt")

logger.debug("Loading model '%s'", MODEL_NAME)
model = whisper.load_model(MODEL_NAME, download_root=MODEL_PATH).to(DEVICE)
logger.debug("Model loaded.")


def process(audio):
  logger.info("Received audio chunk of size %s", len(audio))
  audio = np.frombuffer(audio, np.int16).flatten().astype(np.float32) / 32768.0
  result = model.transcribe(audio, fp16=FP16)
  logger.info("Result: '%s'", result)
  for i, segment in enumerate(result["segments"]):
    logger.info("Segment %s: '%s'", i, segment)
  return result["text"]


async def main():
  async with websockets.connect(os.environ["WSHUB_URI"]) as ws:
    await ws.send("stt")
    while True:
      data = await ws.recv()
      await ws.send(process(data))


asyncio.run(main())
