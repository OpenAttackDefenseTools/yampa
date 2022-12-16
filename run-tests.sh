#!/bin/bash

./generate-env.sh

docker compose --profile testing --env-file .env-test up --build --abort-on-container-exit
