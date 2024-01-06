FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

ARG TARGETARCH
ARG TARGETVARIANT

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN echo "Dir::Cache var/cache/apt/${TARGETARCH}${TARGETVARIANT};" > /etc/apt/apt.conf.d/01cache

RUN --mount=type=cache,id=apt-run,target=/var/cache/apt \
    mkdir -p /var/cache/apt/${TARGETARCH}${TARGETVARIANT}/archives/partial && \
    apt-get update && \
    apt-get install --yes --no-install-recommends \
        python3 python3-pip python3-venv \
        ca-certificates libespeak-ng1 \
        git

RUN useradd -ms /bin/bash mimic3

USER mimic3

RUN mkdir -p /home/mimic3/.local/share/mycroft/mimic3/voices/

WORKDIR /home/mimic3/app

RUN git clone https://github.com/MycroftAI/mimic3.git \
 && mv mimic3/* . \
 && rm -r mimic3

RUN sed -i 's/onnxruntime/onnxruntime-gpu/' ./requirements.txt \
 && echo "websockets" >> ./requirements.txt

RUN --mount=type=cache,id=pip-requirements,target=/root/.cache/pip \
    ./install.sh

COPY run.sh app.py .

ENTRYPOINT ["./run.sh"]
