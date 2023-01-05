#!/bin/bash

./generate-env.sh

ENV_FILE=".env-test" RULES_DIR="./test/rules" PLUGIN_DIR="./test/plugins" docker compose --profile testing up --build --abort-on-container-exit
