#!/usr/bin/bash

function run () {

python3 play.py -player Test

}

cd ..

source venv/bin/activate

run

deactivate

exit
