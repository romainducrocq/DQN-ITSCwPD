#!/usr/bin/bash

cd ..

apt-get update && apt-get install build-essential libpq-dev libssl-dev openssl libffi-dev sqlite3 libsqlite3-dev libbz2-dev zlib1g-dev libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev git g++ cmake

m=0 && while wget -q --method=HEAD https://www.python.org/ftp/python/3.7.$(( $m + 1 ))/Python-3.7.$(( $m + 1 )).tar.xz; do m=$(( $m + 1 )); done && wget https://www.python.org/ftp/python/3.7.$m/Python-3.7.$m.tar.xz && tar xvf Python-3.7.$m.tar.xz && cd Python-3.7.$m && ./configure && make && make altinstall && cd .. && rm -rv Python-3.7.$m.tar.xz Python-3.7.$m

mkdir venv && python3.7 -m venv venv/

source venv/bin/activate

export TMPDIR='/var/tmp'
pip3 install gym torch tensorboard 'msgpack==1.0.2' wheel --no-cache-dir

deactivate

cd venv/ && git clone --recursive https://github.com/eclipse/sumo && rm -rv $(find sumo/ -iname "*.git*")
mkdir sumo/build/cmake-build && cd sumo/build/cmake-build
cmake ../..
make -j$(nproc)

exit
