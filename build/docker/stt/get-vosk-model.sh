#!/usr/bin/bash
stt_vosk_model="vosk-model-en-us-0.42-gigaspeech"
echo "Downloading Speech-to-Text Vosk model: $stt_vosk_model"
curl \
  https://alphacephei.com/vosk/models/$stt_vosk_model.zip \
  --output $stt_vosk_model.zip
unzip $stt_vosk_model.zip
mv $stt_vosk_model res/stt_vosk_model
rm $stt_vosk_model.zip
