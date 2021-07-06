#!/usr/bin/bash

function run () {

python3 play.py -player tmp

}

cd ..

source venv/bin/activate

run

deactivate

exit
