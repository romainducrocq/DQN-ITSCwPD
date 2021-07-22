#!/usr/bin/bash

function run () {

tensorboard --logdir ./logs/train/1tls_4x4/

}

cd ..

source venv/bin/activate

run

deactivate

exit
