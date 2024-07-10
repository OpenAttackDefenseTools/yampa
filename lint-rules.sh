#!/bin/bash

if [ "$1" == "test" ]; then
  RULES_DIR="./test/rules"
else
  RULES_DIR="./rules"
fi

RULES="$(cat $RULES_DIR/*.rls)"

docker compose run -iT --rm yampa filter_engine_lint <<<"$RULES"
