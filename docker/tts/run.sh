#!/bin/bash
/home/mimic3/app/.venv/bin/python3 app.py & \
/home/mimic3/app/.venv/bin/python3 -m mimic3_http \
  --preload-voice en_US/vctk_low \
  --voice ${VOICE} \
  --debug \
  --port ${PORT_1} \
  --cuda & \
wait


