"""
Zaida AI client entrypoint
"""

import os
import asyncio
import websockets
import logging
from concurrent.futures import ThreadPoolExecutor
from ctypes import CFUNCTYPE, cdll, c_int, c_char_p

import speech_recognition as sr
import sounddevice as sd
from dotenv import dotenv_values

ENVS = dotenv_values()

logging.basicConfig(format="%(asctime)s | %(message)s")
logger = logging.getLogger("zaida.client")
logger.setLevel(ENVS["LOG_LEVEL"])

# Supress ALSA warnings and errors from terminal.
# https://stackoverflow.com/questions/7088672#answer-13453192


# pylint: disable=unused-argument
def py_error_handler(filename, line, function, err, fmt):
  pass


make_cfunc = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
c_error_handler = make_cfunc(py_error_handler)
asound = cdll.LoadLibrary("libasound.so")
asound.snd_lib_error_set_handler(c_error_handler)


class ZaidaClient:
  """
  Main class for handling all interactions between the user and the server.
  """

  def __init__(
      self,
      hostname="localhost",
      port=ENVS["PORT_1"],
      energy_threshold=150,
      output_device="pipewire",
  ):

    self.wshub_uri = f"ws://{hostname}:{port}/"
    self.user = os.environ["USER"]
    self.configure_output_stream(output_device)
    self.configure_input_stream(energy_threshold)

  def configure_input_stream(self, energy_threshold):
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
      if name == "pipewire":
        self.mic = sr.Microphone(device_index=index, sample_rate=16000)
        break
    self.rec = sr.Recognizer()
    self.rec.pause_threshold = .6
    self.queue = asyncio.Queue()

    if energy_threshold is None:
      self.calibrate()
    else:
      self.rec.energy_threshold = energy_threshold
      self.rec.dynamic_energy_threshold = False

  def configure_output_stream(self, output_device):
    self.output_device = sd.query_devices(output_device, "output")
    self.output_device_index = self.output_device["index"]

    # settings supported by mimic3
    self.output_channels = 1
    self.bytes_per_sample = 2  # 16 bits
    self.samples_per_second = 22050

    frame_duration = 10
    self.samples_per_frame = (frame_duration * self.samples_per_second) // 1000

    self.output_stream = sd.RawOutputStream(
        samplerate=self.samples_per_second,
        blocksize=self.samples_per_frame,
        device=self.output_device_index,
        channels=self.output_channels,
        dtype="int16",
    )

    self.executor = ThreadPoolExecutor()

  def calibrate(self, duration: float = 3.):
    with self.mic as source:
      logger.info("Calibrating microphone...")
      self.rec.adjust_for_ambient_noise(source, duration=duration)
      logger.info("Microphone calibrated to energy threshold of %s",
                  self.rec.energy_threshold)

  async def listen_forever(self, ws):

    loop = asyncio.get_running_loop()

    def callback(recognizer: sr.Recognizer, audio: sr.AudioData):
      logger.debug("Callback called, putting audio of size %s in queue",
                   len(raw_data := audio.get_raw_data()))
      loop.call_soon_threadsafe(self.queue.put_nowait, raw_data)

    while True:
      self.stop_listening = self.rec.listen_in_background(self.mic, callback)
      try:
        while True:
          logger.debug("Waiting for audio queue...")
          await ws.send(await self.queue.get())
          logger.debug("Audio sent to server.")
      except KeyboardInterrupt:
        self.stop_listening(wait_for_stop=False)
        break

  async def hear_forever(self, ws):

    self.output_stream.start()
    while True:
      async for bytestring in ws:
        try:
          await asyncio.get_event_loop().run_in_executor(
              self.executor,
              self.output_stream.write,
              bytestring,
          )
        except KeyboardInterrupt:
          self.output_stream.stop()

  async def communicate(self):
    async with websockets.connect(
        self.wshub_uri,
        logger=logger,
        max_size=10**9,
    ) as ws:
      await ws.send("client")
      await asyncio.gather(
          self.listen_forever(ws),
          self.hear_forever(ws),
      )

  def run(self):
    asyncio.run(self.communicate())


def main():
  client = ZaidaClient()
  client.run()


if __name__ == "__main__":
  main()
