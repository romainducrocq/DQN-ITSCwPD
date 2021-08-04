#!/usr/bin/bash

function run () {

SAVE="1tls_3x3"

python3 observe.py -d save/$SAVE/DuelingDoubleDQNAgent_lr0.0001_model.pack

}

cd ..

source venv/bin/activate

run

deactivate

exit
