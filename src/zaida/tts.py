"""
Text-to-Speech module with Festival CLI tool
"""

import sounddevice as sd
import subprocess


class TTS:

  def __init__(self):
    self.set_output_device(10)

  def set_output_device(self, index=None):
    if index is None:
      index = int(input(f"Type index of output device:\n{sd.query_devices()}"))
    self.output_device_index = index

  def say(self, text: str):
    p1 = subprocess.Popen(["echo", f'"{text}"'], stdout=subprocess.PIPE)
    self.proc = subprocess.run(["festival", "--tts"], stdin=p1.stdout)

  def is_talking(self):
    return self.proc and self.proc.poll() is None

  def wait(self):
    if self.proc:
      self.proc.wait()

  def quiet(self):
    if self.proc:
      self.proc.terminate()


def main():
  TTS().say("Hello World")


if __name__ == "__main__":
  main()
