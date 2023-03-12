FROM python:3.10

RUN python -m venv /opt/venv \
 && source /opt/venv/bin/activate

RUN curl -sSL https://install.python-poetry.org | python3 - \
 && export PATH="/root/.local/bin/:$PATH"

RUN apt-get update -qq \
 && apt-get install \
    git \
    curl

RUN poetry add git+https://github.com/RasaHQ/rasa.git
