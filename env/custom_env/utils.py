CONFIGS_SIMPLE = [
    "1tls_2x2",
    "1tls_3x3",
    "1tls_4x4"
    # "1tls_5x5"
]

CONFIGS_MULTI = [
    "2tls_3x3x2",
    "3tls_2x2x3",
    "3tls_3x3x3",
    "4tls_3x3x2x2",
    "9tls_3x3x3x3"
]

SUMO_PARAMS = {
    "config": CONFIGS_SIMPLE[1],

    "steps": 3600,
    "delay": 0,
    "gui": True,
    "log": False,
    "rnd": (True, True),
    "seed": False,

    "v_type_def": "def",
    "v_type_con": "con",
    "v_length": 5,
    "v_min_gap": 2.5,
    "v_max_speed": 16.67,

    "veh_p_hour": [200, 800, 800, 200],

    "con_penetration_rate": 1.,
    "con_range": 160,

    "cell_length": 8
}
