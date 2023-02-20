"""
Zaida AI assistant entrypoint
"""

import asyncio

from zaida.nlu import NLUclient
from zaida.tts import TTSclient
from zaida.stt import STTclient


class Zaida:
  """ Zaida AI main class """

  def __init__(self):
    self.nlu = NLUclient("http://localhost:5005")
    self.stt = STTclient("ws://localhost:8765")
    self.tts = TTSclient("http://localhost:59125/api/tts")

  async def listen(self):
    async for text in self.stt.listen():
      print(text, end=" ")

  def run(self):
    asyncio.run(self.listen())


Zaida().run()
