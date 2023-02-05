#!/usr/bin/bash
# https://rasa.com/docs/rasa/action-server/deploy-action-server/#manually-building-an-action-server
docker build . -t mcleonte/rasa-actions:latest
