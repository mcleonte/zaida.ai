#!/bin/bash
/home/mimic3/app/.venv/bin/python3 app.py & \
/home/mimic3/app/.venv/bin/python3 -m mimic3_http --cuda & \
wait


