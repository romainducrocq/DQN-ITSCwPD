#!/usr/bin/bash

cd ../

source venv/bin/activate
tensorboard --logdir ./logs/train/
deactivate

exit
