#!/usr/bin/bash

ALGO="SotlBaseline"

cd ../

source venv/bin/activate
python3 play.py -player $ALGO
deactivate

exit
