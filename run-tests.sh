#!/bin/bash

./generate-env.sh

docker compose --profile testing up --build --abort-on-container-exit
