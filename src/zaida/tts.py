"""
Text-to-Speech module based on Mimic3.
"""

import subprocess


class TTSserver:
  """
  Interface class for communicating with Mimic3 server.
  """

  def __init__(
      self,
      uri=None,
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
    self.args = [
        "curl", "-s", "-X", "POST", "--data", None, "--output", "-", self.uri
    ]

  def say(self, text: str):
    self.args[5] = text
    p1 = subprocess.Popen(self.args, stdout=subprocess.PIPE)
    self.proc = subprocess.run(["aplay", "-q"], stdin=p1.stdout)

  def is_talking(self):
    return self.proc and self.proc.poll() is None

  def wait(self):
    while self.proc:
      pass

  def quiet(self):
    if self.proc:
      self.proc.terminate()


def main(text="Hello World"):
  TTSserver().say(text)


if __name__ == "__main__":
  import sys
  main(sys.argv[-1])
