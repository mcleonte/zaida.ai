FROM mycroftai/mimic3

COPY args.py app.py const.py synthesis.py ./mimic3_http/

ENTRYPOINT ["/home/mimic3/app/.venv/bin/python","-m","mimic3_http","--preload-voice","en_US/vctk_low","--voice","en_US/vctk_low","--speaker","p329"]
