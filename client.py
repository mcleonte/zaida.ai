"""
Zaida AI client entrypoint
"""

import asyncio
import websockets
import requests
import logging
import json
from datetime import datetime
from ctypes import CFUNCTYPE, cdll, c_int, c_char_p

import speech_recognition as sr
import sounddevice as sd

logging.basicConfig(format="%(asctime)s | %(message)s")
logger = logging.getLogger("zaida.client")
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


class ZaidaClient:
  """
  Client class for communicating with the STT websocket server.
  """

  def __init__(
      self,
      hostname="localhost",
      nlu_port=8000,
      stt_port=8080,
      tts_port=8088,
      energy_threshold=150,
      output_device="pipewire",
  ):

    self.nlu_uri = f"http://{hostname}:{nlu_port}"
    self.stt_uri = f"ws://{hostname}:{stt_port}"
    self.tts_uri = f"ws://{hostname}:{tts_port}"

    self.configure_output_stream(output_device)
    self.configure_input_stream(energy_threshold)

  def configure_input_stream(self, energy_threshold):

    self.mic = sr.Microphone(sample_rate=16000)
    self.rec = sr.Recognizer()
    self.rec.pause_threshold = 1
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

  def say(self, bytestring: bytes):
    self.output_stream.start()
    self.output_stream.write(bytestring)
    self.output_stream.stop()

  async def listen_forever(self):

    loop = asyncio.get_running_loop()

    def callback(recognizer: sr.Recognizer, audio: sr.AudioData):
      logger.debug("Callback called, putting audio of size %s in queue",
                   len(raw_data := audio.get_raw_data()))
      loop.call_soon_threadsafe(self.queue.put_nowait, raw_data)

    async with websockets.connect(self.stt_uri, logger=logger) as websocket:
      self.stop_listening = self.rec.listen_in_background(self.mic, callback)
      try:
        while True:
          logger.debug("Waiting for audio queue...")
          await websocket.send(await self.queue.get())
          logger.debug("Audio sent to server.")
      except KeyboardInterrupt:
        self.stop_listening(wait_for_stop=False)

  async def answer_forever(self):

    self.output_stream.start()
    try:
      async with websockets.connect(self.tts_uri, logger=logger) as websocket:
        async for bytestring in websocket:
          self.output_stream.write(bytestring)
    except KeyboardInterrupt:
      self.output_stream.stop()

  async def text_forever(self):

    loop = asyncio.get_running_loop()

    while True:
      text = await loop.run_in_executor(None, lambda: input("You: "))
      print(f"[{datetime.now()}] You: {text}")
      resp = requests.post(
          self.nlu_uri,
          data=json.dumps({
              "message": text,
              "sender": "mcleonte",
          }),
          timeout=None,
      )
      if not resp.ok:
        print(resp.status)
        continue
      resp = resp.json()
      try:
        print(f"[{datetime.now()}] Zaida: {resp[0]['text']}")
      except IndexError:
        print(resp)

  async def communicate(self):
    await asyncio.gather(
        self.listen_forever(),
        self.answer_forever(),
        self.text_forever(),
    )

  def run(self):
    asyncio.run(self.communicate())


def main():
  client = ZaidaClient()
  client.run()


if __name__ == "__main__":
  main()
