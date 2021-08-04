#!/usr/bin/bash

function run () {

SAVE="1tls_3x3"

tensorboard --logdir ./logs/train/$SAVE/

}

cd ..

source venv/bin/activate

run

deactivate

exit
