#!/usr/bin/bash

function run () {

tensorboard --logdir ./logs/train/

}

cd ..

source venv/bin/activate

run

deactivate

exit
