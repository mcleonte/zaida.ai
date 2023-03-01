FROM nvcr.io/nvidia/cuda:11.4.2-cudnn8-devel-ubuntu20.04

COPY --from=mycroftai/mimic3 \
  /home/mimic3/app/.venv \
  /home/mimic3/app/mimic3_http \
  /home/mimic3/app/mimic3_tts \
  /home/mimic3/app/opentts_abc \
  /

RUN source /home/mimic3/app/.venv/bin/activate \
 && pip remove onnxruntime \
 && pip install onnxruntime-gpu

RUN useradd -ms /bin/bash mimic3

USER mimic3

ENTRYPOINT ["/home/mimic3/.venv/bin/python3", "-m", "mimic3_http", "--cuda"]
