#!/usr/bin/bash

function run () {

ALGO="SotlBaseline"

python3 play.py -player $ALGO

}

cd ..

source venv/bin/activate

run

deactivate

exit
