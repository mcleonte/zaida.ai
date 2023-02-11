# Zaida AI voice assistant

## Integrations

- offline Natural Language Understanding with dockerized [Rasa Open Source](https://github.com/RasaHQ/rasa) and [SpaCy](https://spacy.io/models/en#en_core_web_lg) model
- offline Text-to-Speech with dockerized [Mimic3](https://github.com/MycroftAI/mimic3) server
- offline Speech-to-Text with dockerized [Vosk](https://github.com/alphacep/vosk-api) server

## Available features
- real-time Speech-To-Speech interaction
- ask for the current time in any country / city / state supported by SpaCy, or
  just the local time if no location is specified

## Setup

```bash
git clone https://github.com/mcleonte/zaida.ai.git
cd zaida.ai/build/
docker compose up --detach
poetry install
poetry run python -m zaida
```
After your first voice input, if you get a ConnectionError, your should wait a
few more seconds to let all the Docker services to start up, as the NLU service
take a few more seconds longer. After the initialization, interactions should
feel real-time.

## Notes

This is still a very new project, as I've just almost finished polishing the STT and TTS
integrations.
However, there isn't much to go with on the NLU side yet, which I want to focus
on next. So far I plan on developing features for:
- daily tasks and workflows
- window & environment management
- filesystem & browser navigation
- text summarization

and many other will follow.
