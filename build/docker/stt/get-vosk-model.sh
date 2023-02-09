#!/usr/bin/bash
vosk_model="vosk-model-en-us-0.42-gigaspeech"
echo "Downloading Vosk model: $vosk_model"
curl \
  https://alphacephei.com/vosk/models/$vosk_model.zip \
  --output $vosk_model.zip
unzip $vosk_model.zip
rm $vosk_model.zip
mv $vosk_model model
