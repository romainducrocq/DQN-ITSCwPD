#!/usr/bin/bash

function run () {

python3 play.py -player MaxPressureBaseline

}

cd ..

source venv/bin/activate

run

deactivate

exit
