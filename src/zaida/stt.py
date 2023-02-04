"""
Zaida AI module for Speech to text support
"""

import queue
import sounddevice as sd
import webrtcvad
from vosk import Model, KaldiRecognizer
import sys
import json
import numpy as np
from typing import Annotated, Literal
import pathlib

FrameDuration = Annotated[Literal[10, 20, 30], "ms"]


class STT:

  def __init__(self):
    self.set_input_device(10)
    self.set_frame_duration(10)
    self.model = Model(str( \
        pathlib.Path(__file__).parent.parent.parent / "res" / "stt_vosk_model"))
    self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
    self.recognizer.SetWords(False)
    self.vad = webrtcvad.Vad(mode=2)

  def set_input_device(self, index=None):
    if index is None:
      index = int(
          input(
              f"Type index to choose input device:\n\n{sd.query_devices()}\n\n")
      )  #sd.default.device[0]
    self.input_device_index = index
    self.input_device = sd.query_devices(index, "input")
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

  def listen(self):
    q = queue.Queue()

    def record_callback(indata, frames: int, time, status) -> None:
      if status:
        print(status, file=sys.stderr)
      #byte_data = bytes(indata)
      #if self.vad.is_speech(byte_data, self.sample_rate,
      #                      self.samples_per_frame):
      q.put(bytes(indata))  #.tobytes())
      #else:
      #  q.put(self.silence)

    with sd.RawInputStream(
        samplerate=self.sample_rate,
        blocksize=self.samples_per_frame,
        dtype=np.int16,
        device=self.input_device_index,
        channels=self.input_channels,
        callback=record_callback,
    ):
      while True:
        if self.recognizer.AcceptWaveform(q.get()):
          result = json.loads(self.recognizer.Result())
          if result["text"]:
            yield result["text"], True
        else:
          result = json.loads(self.recognizer.PartialResult())
          yield result["partial"], False


def main():
  for text, is_final in STT().listen():
    if is_final:
      print("\n", text, sep="")
    else:
      print(f"partial: {text}\r", end="")


if __name__ == "__main__":
  main()
