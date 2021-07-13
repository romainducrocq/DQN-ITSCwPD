#!/usr/bin/bash

function run () {

tensorboard --logdir ./logs/train/1tls_3x3/rew3_delay_sq/

}

cd ..

source venv/bin/activate

run

deactivate

exit
