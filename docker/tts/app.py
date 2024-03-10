"""
TTS websocket client module
"""

import os
import requests
import asyncio
import logging
import websockets

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


def process(text):
  response = requests.post(
      f"http://localhost:{ os.environ['PORT_1'] }/api/tts",
      json={
          "text": text,
          "voice": os.environ["VOICE"],
      },
      timeout=None,
  )
  return response.content


async def main():
  async with websockets.connect(os.environ["WSHUB_URI"]) as ws:
    await ws.send("tts")
    while True:
      data = await ws.recv()
      await ws.send(process(data))


asyncio.run(main())
