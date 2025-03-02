#!/usr/bin/bash

ALGO="SotlBaseline"

cd ../

source venv/bin/activate
if [ -z "${1}" ]; then
    python3 play.py -player $ALGO
else
    python3 play.py "${@}"
fi
deactivate

exit
