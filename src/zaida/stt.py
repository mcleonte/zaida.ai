"""
Speech-to-Text module
"""

import sounddevice as sd
import websockets
import asyncio
import sys
import json
from typing import Annotated, Literal
import webrtcvad
import numpy as np
from speech_recognition import AudioData

FrameDuration = Annotated[Literal[10, 20, 30], "ms"]


class STTserver:
  """
  Interface class for communicating with Vosk server.
  """

  def __init__(
      self,
      uri=None,
      protocol="ws",
      hostname="localhost",
      port=8765,
      input_device=None,
  ):

    if uri is None:
      uri = f"{protocol}://{hostname}:{port}"
    self.uri = uri

    self.set_input_device(input_device)
    self.set_frame_duration(30)

    self.vad = webrtcvad.Vad()
    self.vad.set_mode(2)
    self.pause_frames = 0

  def set_input_device(self, device=None):
    if device is None:
      device = input(
          f"Type index to choose input device:\n\n{sd.query_devices()}\n\n")
    try:
      device = int(device)
    except:
      pass
    self.input_device = sd.query_devices(device, "input")
    self.input_device_index = self.input_device["index"]
    self.samples_per_second = 16000  # int(self.input_device["default_samplerate"])
    self.input_channels = 1  # int(self.input_device["max_input_channels"])
    print(f"Input device selected: {self.input_device}")

  def set_frame_duration(self, frame_duration: FrameDuration = 10):
    self.frame_duration = frame_duration
    self.samples_per_frame = frame_duration * self.samples_per_second // 1000
    self.frames_per_second = 1000 / frame_duration

  async def listen(self):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    # pylint: disable=unused-argument
    def callback(indata, frames: int, time, status) -> None:
      if self.vad.is_speech(indata, self.samples_per_second):
        self.pause_frames = 0
        loop.call_soon_threadsafe(queue.put_nowait, indata)
      else:
        self.pause_frames += 1
        loop.call_soon_threadsafe(queue.put_nowait, b"")

    with sd.RawInputStream(
        samplerate=self.samples_per_second,
        blocksize=self.samples_per_frame,
        dtype="int16",
        device=self.input_device_index,
        channels=self.input_channels,
        callback=callback,
    ):

      async with websockets.connect(self.uri) as websocket:

        # await websocket.send(
        #     json.dumps({"config": {
        #         "sample_rate": device.samplerate
        #     }}))

        chunks = []
        while True:
          if chunk := await queue.get():
            chunks.append(chunk)

          print(f"{self.pause_frames}, {len(chunks)}   \r", end="")
          if not chunks or self.pause_frames < 10:
            continue

          audio = AudioData(b"".join(chunks), self.samples_per_second, 2)
          await websocket.send(audio.get_raw_data())
          yield await websocket.recv()
          chunks = []


async def main():
  async for text in STTserver(input_device="pipewire").listen():
    print(f"\n{text}")
  # async for text, is_partial in STTserver().listen():
  #   if is_partial:
  #     print(f"partial: {text}\r", end="")
  #     continue
  #   elif text:
  #     print("\n", text, sep="")


if __name__ == "__main__":
  asyncio.run(main())
