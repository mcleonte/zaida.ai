"""
Zaida AI Speech-to-Text module
"""

import asyncio
import speech_recognition as sr
import websockets
import logging
from ctypes import CFUNCTYPE, cdll, c_int, c_char_p

logging.basicConfig(format="%(asctime)s | %(message)s")
logger = logging.getLogger("zaida.stt")
logger.setLevel(logging.INFO)

# Supress ALSA warnings and errors from terminal.
# https://stackoverflow.com/questions/7088672#answer-13453192


# pylint: disable=unused-argument
def py_error_handler(filename, line, function, err, fmt):
  pass


make_cfunc = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
c_error_handler = make_cfunc(py_error_handler)
asound = cdll.LoadLibrary("libasound.so")
asound.snd_lib_error_set_handler(c_error_handler)


class STTclient:
  """
  Client class for communicating with the STT websocket server.
  """

  def __init__(
    self,
    uri=None,
    protocol="ws",
    hostname="localhost",
    port=8765,
    energy_threshold=150,
  ):

    if uri is None:
      uri = f"{protocol}://{hostname}:{port}"
    self.uri = uri

    self.mic = sr.Microphone(sample_rate=16000)
    self.rec = sr.Recognizer()
    self.rec.pause_threshold = 1
    self.queue = asyncio.Queue()

    if energy_threshold is None:
      self.calibrate()
    else:
      self.rec.energy_threshold = energy_threshold
      self.rec.dynamic_energy_threshold = False

  def calibrate(self, duration: float = 3.):
    with self.mic as source:
      logger.info("Calibrating microphone...")
      self.rec.adjust_for_ambient_noise(source, duration=duration)
      logger.info("Microphone calibrated to energy threshold of %s",
                  self.rec.energy_threshold)

  async def listen(self):

    loop = asyncio.get_running_loop()

    def callback(recognizer: sr.Recognizer, audio: sr.AudioData):
      logger.info("Callback called, putting audio of size %s in queue",
                  len(raw_data := audio.get_raw_data()))
      loop.call_soon_threadsafe(self.queue.put_nowait, raw_data)
      logger.info("Queue increased: %s", self.queue.qsize())

    async with websockets.connect(self.uri, logger=logger) as websocket:
      self.stop_listening = self.rec.listen_in_background(self.mic, callback)
      try:
        while True:
          logger.info("Waiting for audio queue to send to server...")
          audio = await self.queue.get()
          await websocket.send(audio)
          logger.info("Sent to server, waiting to receive transcription...")
          yield await websocket.recv()
      except KeyboardInterrupt:
        self.stop_listening(wait_for_stop=False)


async def main():
  async for text in STTclient().listen():
    print(text)


if __name__ == "__main__":
  asyncio.run(main())
