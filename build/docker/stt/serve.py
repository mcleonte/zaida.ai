"""
Speech to text websocket server module
"""

import logging
import asyncio
import websockets
import numpy as np
import torch
import whisper
import os

PORT = os.environ["PORT"] or 8765
MODEL_NAME = os.environ["MODEL_NAME"] or "small.en"
MODEL_PATH = os.environ["MODEL_PATH"] or "/app/models/"
FP16 = torch.cuda.is_available()

logger = logging.getLogger("STTserver")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

logger.info("Loading model '%s'", MODEL_NAME)
model = whisper.load_model(MODEL_NAME, download_root=MODEL_PATH)
logger.info("Model loaded.")


async def transcribe(websocket):
  async for audio in websocket:
    logger.info("Received audio chunk of size %s", len(audio))
    audio = np.frombuffer(audio, np.int16).flatten().astype(
        np.float32) / 32768.0
    result = model.transcribe(audio, fp16=FP16)
    logger.info("Result: '%s'", result)
    for i, segment in enumerate(result["segments"]):
      logger.info("Segment %s: '%s'", i, segment)
    await websocket.send(result["text"])


async def main():
  async with websockets.serve(transcribe, "0.0.0.0", PORT, logger=logger):
    await asyncio.Future()


asyncio.run(main())
