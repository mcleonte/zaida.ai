from zaida.tts import TTS
from zaida.stt import STT

tts = TTS()
stt = STT()

for text, is_final in stt.listen():
  if is_final:
    print("\n", text, sep="")
    tts.say(text)
  else:
    print(f"partial: {text}\r", end="")
