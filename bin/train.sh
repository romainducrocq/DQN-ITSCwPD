#!/usr/bin/bash

cd ../

source venv/bin/activate
python3 train.py -algo DuelingDoubleDQNAgent -max_total_steps 4000000
deactivate

exit
