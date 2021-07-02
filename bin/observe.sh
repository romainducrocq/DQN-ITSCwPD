#!/usr/bin/bash

function run () {

python3 observe.py -d save/PerDuelingDoubleDQNAgent_lr0.0001_model.pack

}

cd ..

source venv/bin/activate

run

deactivate

exit
