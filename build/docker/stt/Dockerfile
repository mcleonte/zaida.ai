FROM python:3.10

WORKDIR /app/

COPY requirements.txt serve.py tests_jfk.flac .

RUN apt-get -y update && apt-get install ffmpeg -y

RUN pip install -r requirements.txt

RUN whisper --model small.en -f txt tests_jfk.flac

CMD ["python", "serve.py"]
