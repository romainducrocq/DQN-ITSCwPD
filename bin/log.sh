#!/usr/bin/bash

function run () {

MAX_E="10"
CONF="1tls_3x3"
DIR="con"

python3 observe.py -d save/$CONF/DuelingDoubleDQNAgent_lr0.0001_model.pack -max_e $MAX_E -log y -log_s 1 -log_dir ./logs/test/$CONF/$DIR/ && python3 play.py -player MaxPressureBaseline -max_e $MAX_E -log y -log_s 1 -log_dir ./logs/test/$CONF/$DIR/ && python3 play.py -player SotlBaseline -max_e $MAX_E -log y -log_s 1 -log_dir ./logs/test/$CONF/$DIR/ && python3 play.py -player UniformBaseline -max_e $MAX_E -log y -log_s 1 -log_dir ./logs/test/$CONF/$DIR/

}

cd ..

source venv/bin/activate

run

deactivate

exit
