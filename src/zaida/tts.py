"""
Zaida AI Text-to-Speech module.
"""

import sys
import subprocess
import sounddevice as sd
import requests
import asyncio
import pyperclip


class TTSclient:
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

  def say(self, text: str):
    data = requests.post(
        self.uri,
        text.encode("utf-8"),
        timeout=None,
    )._content
    self.stream.start()
    self.stream.write(data)
    self.stream.stop()


def main(text="Hello World"):
  if text == "clip":
    text = pyperclip.paste()
  TTSclient().say(text)


if __name__ == "__main__":
  main(sys.argv[-1])
