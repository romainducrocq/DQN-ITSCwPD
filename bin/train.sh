#!/usr/bin/bash

function run () {

python3 train.py -algo DuelingDoubleDQNAgent -max_total_steps 4000000

}

cd ..

source venv/bin/activate

run

deactivate

exit
