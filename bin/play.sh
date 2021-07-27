#!/usr/bin/bash

function run () {

python3 play.py -player SotlBaseline -max_e 1000 -log y -log_s 1 -log_dir ./logs/test/1tls_3x3/con/

}

cd ..

source venv/bin/activate

run

deactivate

exit
