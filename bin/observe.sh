#!/usr/bin/bash

SAVE="1tls_3x3"

cd ../

source venv/bin/activate
python3 observe.py -d save/$SAVE/DuelingDoubleDQNAgent_lr0.0001_model.pack
deactivate

exit
