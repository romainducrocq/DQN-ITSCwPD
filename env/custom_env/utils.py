import json

CONFIGS_SIMPLE = [
    "1tls_2x2",
    "1tls_3x3",
    "1tls_4x4",
    "1tls_5x5"
]

CONFIGS_MULTI = [
    "2tls_3x3x2",
    "3tls_2x2x3",
    "3tls_3x3x3",
    "4tls_3x3x2x2",
    "9tls_3x3x3x3"
]

SUMO_PARAMS = {
    "config": CONFIGS_SIMPLE[2],

    "steps": 3600,
    "delay": 0,
    "gui": True,

    "v_type_def": "def",
    "v_type_con": "con",

    "veh_co_p": 0.3
}


def pretty_print(d):
    print(json.dumps(d, sort_keys=True, indent=4))
