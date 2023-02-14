"""
Text-to-Speech module based on Mimic3.
"""

import subprocess
import sys
import sounddevice as sd
from typing import Annotated, Literal
import requests
import asyncio


class TTSserver:
  """
  Interface class for communicating with Mimic3 server.
  """

  def __init__(
      self,
      uri=None,
      output_device="pipewire",
      protocol="http",
      hostname="localhost",
      port=59125,
      endpoint="/api/tts",
      voice=None,  #"en_US/vctk_low",
      speaker=None,  #"p329",
  ):

    if uri is None:
      uri = f"{protocol}://{hostname}:{port}{endpoint}"
    if voice and speaker:
      uri += f"?voice={voice}&speaker={speaker}"
    self.uri = uri

    self.output_device = sd.query_devices(output_device, "output")
    self.output_device_index = self.output_device["index"]

    # settings supported by mimic3
    self.output_channels = 1
    self.bytes_per_sample = 2  # 16 bits
    self.samples_per_second = 22050

    frame_duration = 10
    self.samples_per_frame = (frame_duration * self.samples_per_second) // 1000

    self.stream = sd.RawOutputStream(
        samplerate=self.samples_per_second,
        blocksize=self.samples_per_frame,
        device=self.output_device_index,
        channels=self.output_channels,
        dtype="int16",
    )

  async def say(self, text: str):
    data = requests.post(self.uri, text)._content
    self.stream.start()
    self.stream.write(data)
    self.stream.stop()


async def main(text="Hello World"):
  await TTSserver().say(text)


if __name__ == "__main__":
  asyncio.run(main(sys.argv[-1]))
