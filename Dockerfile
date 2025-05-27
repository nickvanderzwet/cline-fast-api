FROM python:3.9-slim-buster

WORKDIR /app

COPY ./db_utils.py /app/db_utils.py
COPY ./main.py /app/main.py
COPY ./requirements.txt /app/requirements.txt
COPY ./init.sql /app/init.sql

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "/app/main.py"]
