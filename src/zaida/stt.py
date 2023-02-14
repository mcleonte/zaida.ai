"""
Speech-to-Text module with Vosk
"""

import sounddevice as sd
import websockets
import asyncio
import sys
import json
from typing import Annotated, Literal

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
      port=2700,
      input_device=None,  #"eah-az60",
  ):

    if uri is None:
      uri = f"{protocol}://{hostname}:{port}"
    self.uri = uri

    self.set_input_device(input_device)
    self.set_frame_duration(10)

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
    self.sample_rate = int(self.input_device["default_samplerate"])
    self.input_channels = int(self.input_device["max_input_channels"])
    print(f"Input device selected: {self.input_device}")

  def set_frame_duration(self, frame_duration: FrameDuration = 10):
    self.frame_duration = frame_duration
    self.samples_per_frame = frame_duration * self.sample_rate // 1000
    self.frames_per_second = 1000 / frame_duration
    self.silence = b"\x00" * self.samples_per_frame

  def get_input_devices(self):
    print(sd.query_devices())

  async def listen(self):

    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    def callback(indata, frames: int, time, status) -> None:
      loop.call_soon_threadsafe(queue.put_nowait, bytes(indata))

    with sd.RawInputStream(
        samplerate=self.sample_rate,
        blocksize=self.samples_per_frame,
        dtype="int16",
        device=self.input_device_index,
        channels=self.input_channels,
        callback=callback,
    ) as device:

      async with websockets.connect(self.uri) as websocket:

        await websocket.send(
            json.dumps({"config": {
                "sample_rate": device.samplerate
            }}))

        while True:
          await websocket.send(await queue.get())
          result = json.loads(await websocket.recv())
          if "partial" in result:
            yield result["partial"], True
            continue
          yield result["text"], False


async def main():
  async for text, is_partial in STTserver().listen():
    if is_partial:
      print(f"partial: {text}\r", end="")
      continue
    elif text:
      print("\n", text, sep="")


if __name__ == "__main__":
  asyncio.run(main())
