#!/usr/bin/bash

function run () {

python3 observe.py -d save/1tls_3x3/DuelingDoubleDQNAgent_lr0.0001_eps_min_0.1_eps_dec_1e5_model.pack

}

cd ..

source venv/bin/activate

run

deactivate

exit
