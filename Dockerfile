FROM python:3.11-slim AS builder

RUN python3 -m venv /venv

RUN apt-get update && apt-get install -y git curl build-essential

RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

ENV PATH="/root/.cargo/bin:/venv/bin:${PATH}"

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt


FROM python:3.11-slim

ENV PATH="/venv/bin:$PATH"

WORKDIR /

VOLUME /yamp/plugins

COPY --from=builder /venv /venv
COPY yamp /yamp

CMD [ "bash", "-c", "sleep 0.5 && exec python -m yamp" ]
