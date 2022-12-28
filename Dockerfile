FROM python:3.11-slim AS builder

RUN python3 -m venv /venv

RUN apt-get update && apt-get install -y git curl build-essential

RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

ENV PATH="/root/.cargo/bin:/venv/bin:${PATH}"

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

COPY filter_engine /filter_engine

RUN pip install --no-cache-dir /filter_engine

FROM python:3.11-slim

ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/dependencies:$PYTHONPATH"

WORKDIR /

VOLUME /plugins
VOLUME /dependencies

COPY --from=builder /venv /venv
COPY yamp /yamp

CMD [ "bash", "-c", "sleep 0.5 && exec python -m yamp" ]
