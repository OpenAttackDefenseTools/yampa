FROM python:3.11-slim

RUN python3 -m venv /venv

RUN apt-get update && apt-get install -y iproute2 wireguard-tools

ENV PATH="/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

COPY . /app

CMD [ "bash", "/app/start.sh" ]
