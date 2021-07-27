#!/usr/bin/bash

function run () {

python3 observe.py -d save/1tls_3x3/DuelingDoubleDQNAgent_lr0.0001_model.pack -max_e 10 -log y -log_s 1 -log_dir ./logs/test/1tls_3x3/

}

cd ..

source venv/bin/activate

run

deactivate

exit
