FROM pytorch/pytorch:latest

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir rasa-sdk==3.4.0 \
 && pip install --no-cache-dir -r requirements.txt

COPY endpoint.py /opt/conda/lib/python3.10/site-packages/rasa_sdk/
COPY actions actions

# update permissions & change user
RUN chgrp -R 0 /app && chmod -R g=u /app
USER 1001
RUN mkdir /app/.cache/

ENTRYPOINT ["python","-m","rasa_sdk", "--actions", "actions"]
