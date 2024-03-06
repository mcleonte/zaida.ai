"""
TTS websocket client module
"""

import os
import requests
import asyncio
import logging
import websockets

logging.basicConfig(format="%(asctime)s | %(message)s")
logger = logging.getLogger("zaida.wshub")
logger.setLevel(os.environ["LOG_LEVEL"])
logger.addHandler(logging.StreamHandler())


def process(text):
  response = requests.post(
      f"http://localhost:{ os.environ['PORT_1'] }/api/tts",
      json={
          "text": text,
          "voice": os.environ["VOICE"],
      },
  )
  # logger.debug(response.content)  #text)
  return response.content  #text.encode("utf-8")


async def main():
  async with websockets.connect(os.environ["WSHUB_URI"]) as ws:
    # Send the identifier as the first message
    await ws.send("tts")
    while True:
      data = await ws.recv()
      await ws.send(process(data))


asyncio.run(main())
