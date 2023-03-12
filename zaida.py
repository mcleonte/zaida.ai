"""
Zaida AI client entrypoint
"""

import os
import asyncio
import websockets
import aiohttp
import logging
from datetime import datetime
from ctypes import CFUNCTYPE, cdll, c_int, c_char_p

import speech_recognition as sr
import sounddevice as sd
import pyperclip

logging.basicConfig(format="%(asctime)s | %(message)s")
logger = logging.getLogger("zaida.client")
logger.setLevel(logging.DEBUG)

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
      port=8000,
      energy_threshold=150,
      output_device="pipewire",
  ):

    self.stt_uri = f"ws://{hostname}:{port}/stt"
    self.tts_uri = f"ws://{hostname}:{port}/tts"
    self.nlu_uri = f"http://{hostname}:{port}/nlu"
    self.nlu_actions_uri = f"ws://{hostname}:{port}/nlu-actions"

    self.user = os.environ["USER"]

    self.configure_output_stream(output_device)
    self.configure_input_stream(energy_threshold)

  def configure_input_stream(self, energy_threshold):

    self.mic = sr.Microphone(sample_rate=16000)
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

  def calibrate(self, duration: float = 3.):
    with self.mic as source:
      logger.info("Calibrating microphone...")
      self.rec.adjust_for_ambient_noise(source, duration=duration)
      logger.info("Microphone calibrated to energy threshold of %s",
                  self.rec.energy_threshold)

  async def listen_forever(self):

    loop = asyncio.get_running_loop()

    def callback(recognizer: sr.Recognizer, audio: sr.AudioData):
      logger.debug("Callback called, putting audio of size %s in queue",
                   len(raw_data := audio.get_raw_data()))
      loop.call_soon_threadsafe(self.queue.put_nowait, raw_data)

    async with websockets.connect(self.stt_uri, logger=logger) as ws:
      self.stop_listening = self.rec.listen_in_background(self.mic, callback)
      try:
        while True:
          logger.debug("Waiting for audio queue...")
          await ws.send(await self.queue.get())
          logger.debug("Audio sent to server.")
      except KeyboardInterrupt:
        self.stop_listening(wait_for_stop=False)

  async def answer_forever(self):

    self.output_stream.start()
    try:
      async with websockets.connect(self.tts_uri, logger=logger) as ws:
        async for bytestring in ws:
          self.output_stream.write(bytestring)
    except KeyboardInterrupt:
      self.output_stream.stop()

  async def text_forever(self):

    loop = asyncio.get_running_loop()
    data = { "message": None, "sender": self.user }

    async with aiohttp.ClientSession() as session:
      while True:
        text = await loop.run_in_executor(None, lambda: input("You: "))
        data["message"] = text
        print(f"[{datetime.now()}] You: {text}")
        async with session.post(self.nlu_uri, json=data) as resp:
          resp = await resp.json()
        try:
          print(f"[{datetime.now()}] Zaida: {resp[0]['text']}")
        except IndexError:
          print(resp)

  async def execute_forever(self):

    async with websockets.connect(self.nlu_actions_uri, logger=logger) as ws:
      logger.info("Connected to nlu-actions websocket")
      while True:
        logger.debug("Waiting for instruction...")
        instruction = await ws.recv()
      # async for instruction in ws:
        logger.debug("Received instruction: %s",instruction)
        match instruction:
          case "get_clipboard":
            await ws.send(pyperclip.paste())
          case _:
            logger.debug("Instruction not understood: %s", instruction)


  async def communicate(self):
    await asyncio.gather(
        self.listen_forever(),
        self.answer_forever(),
        self.text_forever(),
        self.execute_forever(),
    )

  def run(self):
    asyncio.run(self.communicate())


def main():
  client = ZaidaClient()
  client.run()


if __name__ == "__main__":
  main()
