# Zaida AI voice assistant

## Architecture

To ensure minimal resource usage on the client side, scalability, and the
ability to easily incorporate new features in the future, a Microservice
Architecture was adopted for this project's server implementation. Each
integration is implemented as a decoupled microservice that runs in a
containerized environment with preloaded models and/or other resources for
efficient processing and no load times during inference. The orchestration of
these microservices is currently [configured](https://github.com/mcleonte/zaida.ai/blob/main/build/docker-compose.yml) with Docker Compose.

Details on current integrations:
- offline Speech-to-Text with [OpenAI Whisper](https://github.com/openai/whisper)
   - configured for processing audio device input streams in real time
   - custom Docker image with a minimal [serve.py](https://github.com/mcleonte/zaida.ai/blob/main/build/docker/stt/serve.py) module
   - WebSocket protocol support with [websockets](https://websockets.readthedocs.io) library
   - asynchronous voice recording (client side) and transcription (server side) with [asyncio](https://docs.python.org/3/library/asyncio.html) library
- offline Text-to-Speech with [MycroftAI Mimic3](https://github.com/MycroftAI/mimic3)
- offline Natural Language Understanding with [Rasa Open Source](https://github.com/RasaHQ/rasa) and [SpaCy](https://spacy.io/models/en#en_core_web_lg)
## Features
- real-time Speech-To-Speech interaction
- ask for the current time in any country / city / state supported by SpaCy, or
  just the local time if no location is specified

## Setup

```bash
git clone https://github.com/mcleonte/zaida.ai.git
cd zaida.ai
docker compose up  # add --detach flag or run it in another terminal
./nlu-train.sh
poetry install

# Option 1
poetry run zaida

# Option 2
poetry shell  # or "source .venv/bin/activate"
zaida
```
If `./nlu-train.sh` fails with a ConnectionError, your should wait a
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
