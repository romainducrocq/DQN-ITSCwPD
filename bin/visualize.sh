#!/usr/bin/bash

cd ../

source venv/bin/activate
if [ -z "${1}" ]; then
    tensorboard --logdir ./logs/train/
else
    tensorboard "${@}"
fi
deactivate

exit
