"""
Zaida AI assistant entrypoint
"""

import asyncio
import logging

from zaida.nlu import NLUserver
from zaida.tts import TTSserver
from zaida.stt import STTserver


class Zaida:
  """ Zaida AI main class """

  def __init__(self):
    self.nlu = NLUserver("http://localhost:5005")
    self.stt = STTserver("ws://localhost:8765")
    self.tts = TTSserver("http://localhost:59125/api/tts")

  async def listen(self):
    async for text, is_partial in self.stt.listen():
      if is_partial:
        print(f"partial: {text}\r", end="")
      elif text:
        print("\n", text, sep="")
        resp = self.nlu.interpret(text)
        print(resp)
        self.tts.say(resp)

  def run(self):
    asyncio.run(self.listen())


Zaida().run()
