FROM mycroftai/mimic3

USER root

RUN mkdir -p /home/mimic3/.local/share/mycroft/mimic3/voices/

USER mimic3

COPY __main__.py app.py mimic3_http/
