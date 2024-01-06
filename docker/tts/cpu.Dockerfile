FROM mycroftai/mimic3

USER root

RUN mkdir -p /home/mimic3/.local/share/mycroft/mimic3/voices/

USER mimic3

COPY run.sh app.py .

ENTRYPOINT ["./run.sh"]
