import json

CONFIGS = [
    "1tls_2x2",
    "1tls_3x3",
    "1tls_4x4",
    "1tls_5x5",
    "2tls_3x3x2",
    "3tls_2x2x3",
    "3tls_3x3x3",
    "4tls_3x3x2x2",
    "9tls_3x3x3x3"
]

SUMO_PARAMS = {
    "steps": 3600,
    "delay": 0,
    "gui": True,

    "config": CONFIGS[1],
    "veh_ph": 2000,
    "tg": 5,
    "ty": 3
}


def pretty_print(d):
    print(json.dumps(d, sort_keys=True, indent=4))


def arg_max(_list):
    return max(range(len(_list)), key=lambda i: _list[i])
