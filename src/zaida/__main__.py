"""
Zaida AI assistant entrypoint
"""

from zaida.tts import TTS
from zaida.stt import STT
from zaida.nlu import NLU

tts = TTS()
stt = STT()
nlu = NLU()

for text, is_final in stt.listen():
  if is_final:
    print("\n", text, sep="")
    resp = nlu.interpret(text)
    print(resp)
    tts.say(resp)
  else:
    print(f"partial: {text}\r", end="")
