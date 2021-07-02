#!/usr/bin/bash

function run () {

python3 play.py -player UniformBaseline

}

cd ..

source venv/bin/activate

run

deactivate

exit
