"""
Zaida AI assistant entrypoint
"""

import asyncio
import logging

from zaida.nlu import NLUclient
from zaida.tts import TTSclient
from zaida.stt import STTclient

logger = logging.getLogger("zaida")
logger.setLevel(logging.INFO)


class Zaida:
  """ Zaida AI main class """

  def __init__(self):
    self.nlu = NLUclient("http://localhost:5005")
    self.stt = STTclient("ws://localhost:8765")
    self.tts = TTSclient("http://localhost:59125/api/tts")

  async def listen(self):
    async for text in self.stt.listen():
      logging.debug(text)
      resp = self.nlu.interpret(text)
      logging.debug(resp)
      self.tts.say(resp)

  def run(self):
    asyncio.run(self.listen())


Zaida().run()
