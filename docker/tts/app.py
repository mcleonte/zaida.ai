"""
TTS websocket client module
"""

import os
import requests
import asyncio
import logging
import websockets

logging.basicConfig(
    format="%(asctime)s | %(message)s",
    level=os.environ.get("LOG_LEVEL"),
)
logger = logging.getLogger("zaida.tts")


def process(text):
  response = requests.post(
      f"http://localhost:{ os.environ['PORT_1'] }/api/tts",
      json={
          "text": text,
          "voice": os.environ["VOICE"],
      },
      timeout=None,
  )
  return response.content  #text.encode("utf-8")


async def main():
  async with websockets.connect(os.environ["WSHUB_URI"]) as ws:
    # Send the identifier as the first message
    await ws.send("tts")
    while True:
      data = await ws.recv()
      await ws.send(process(data))


asyncio.run(main())
