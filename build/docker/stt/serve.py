"""
Speech to text websocket server module
"""

import logging
import asyncio
import websockets
import numpy as np
import torch
import whisper

PORT = 8765
MODEL = "small.en"
FP16 = torch.cuda.is_available()

logger = logging.getLogger("STTserver")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

logger.info("Loading model '%s'", MODEL)
model = whisper.load_model(MODEL)
logger.info("Model loaded.")


async def transcribe(websocket):
  async for audio in websocket:
    logger.debug("Received audio chunk of size %s", len(audio))
    audio = np.frombuffer(audio, np.int16).flatten().astype(
        np.float32) / 32768.0
    result = model.transcribe(audio, fp16=FP16)
    logger.debug("Result: '%s'", result)
    await websocket.send(result["text"])


async def main():
  async with websockets.serve(transcribe, "0.0.0.0", PORT, logger=logger):
    await asyncio.Future()


asyncio.run(main())
