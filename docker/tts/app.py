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
  response = requests.get(
      "http://localhost:59125/api/tts",
      params={
          "text": text,
          "voice": "en_US/vctk_low#p329",
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
