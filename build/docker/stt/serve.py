import websockets
import asyncio
import whisper
import logging
import numpy as np

PORT = 8765

logger = logging.getLogger("STTserver")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

logger.info("Model loading...")
model = whisper.load_model("small.en")
logger.info("Model loaded.")


async def transcribe(websocket, path=None):
  async for audio in websocket:
    audio = np.frombuffer(audio, dtype=np.int16)
    result = model.transcribe(audio)
    logger.info(result)
    await websocket.send(result)


async def main():
  async with websockets.serve(transcribe, "0.0.0.0", PORT):
    logger.info(f"STTserver listening on port {PORT}")
    await asyncio.Future()


# if __name__ == "__main__":
asyncio.run(main())
