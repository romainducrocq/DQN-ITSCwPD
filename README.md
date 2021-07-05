## DQN - Intelligent Traffic Signal Control with Partial Detection

****

Implemented from my DQN framework: https://github.com/romainducrocq/frameworQ

****

### Build dependencies

make: `cd bin/ && bash make.sh`

- Python 3.7  
> sudo apt-get update && sudo apt-get install build-essential libpq-dev libssl-dev openssl libffi-dev sqlite3 libsqlite3-dev libbz2-dev zlib1g-dev libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev git g++ cmake python3.7 python3-pip python3.7-dev python3.7-venv  

- venv  
> mkdir venv && python3.7 -m venv venv/  
> source venv/bin/activate  
> deactivate  

- gym, torch, tensorboard, msgpack, wheel  
> (venv) pip3 install gym torch tensorboard 'msgpack==1.0.2' wheel --no-cache-dir  

- sumo  
> cd venv/ && git clone --recursive https://github.com/eclipse/sumo && rm -rv $(find sumo/ -iname "*.git*")  
> mkdir sumo/build/cmake-build && cd sumo/build/cmake-build  
> cmake ../..  
> make -j$(nproc)  
