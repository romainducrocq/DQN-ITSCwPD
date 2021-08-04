#!/usr/bin/bash

function run () {

MAX_E="1000"
SAVE="1tls_3x3"
CONF="4tls_3x3x2x2"
DIR="def"

python3 observe.py -d save/$SAVE/DuelingDoubleDQNAgent_lr0.0001_model.pack -max_e $MAX_E -log y -log_s 1 -log_dir ./logs/test/$CONF/$DIR/ && python3 play.py -player MaxPressureBaseline -max_e $MAX_E -log y -log_s 1 -log_dir ./logs/test/$CONF/$DIR/ && python3 play.py -player SotlBaseline -max_e $MAX_E -log y -log_s 1 -log_dir ./logs/test/$CONF/$DIR/

}

cd ../..

source venv/bin/activate

run

deactivate

exit
