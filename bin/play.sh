#!/usr/bin/bash

function run () {

python3 play.py -player SotlBaseline

}

cd ..

source venv/bin/activate

run

deactivate

exit
