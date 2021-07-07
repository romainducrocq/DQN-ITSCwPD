from .tl_scheduler import TlScheduler
from .sumo_env import SumoEnv

import random
from collections import deque

import numpy as np


class RLController(SumoEnv):
    def __init__(self, *args, **kwargs):
        super(RLController, self).__init__(*args, **kwargs)

        self.tg = 10
        self.ty = 3
        self.tr = 2

        self.dtse_shape = self.get_dtse_shape()
        self.rew_min = 0

        self.scheduler, self.next_tl_id = None, None

        self.action_space_n = len(self.tl_logic[self.tl_ids[0]]["act"])
        self.observation_space_n = 1

    def reset(self):
        self.simulation_reset()

        self.scheduler = TlScheduler(self.tg + self.ty + self.tr, self.tl_ids)
        self.next_tl_id = self.scheduler.pop()[0]

        for _ in range(self.tg):
            self.simulation_step()

    def step(self, action):
        action = random.randint(0, 3)

        tl_id = self.next_tl_id

        if self.tl_logic[tl_id]["act"][action] == self.get_ryg_state(tl_id):
            self.scheduler.push(self.tg, (tl_id, None))
            self.set_phase_duration(tl_id, self.tg)

        else:
            for evt in [
                (self.ty, (tl_id, (self.get_next_red_phase_id(tl_id), self.tr))),
                (self.ty + self.tr, (tl_id, (self.get_new_green_phase_id(tl_id, self.tl_logic[tl_id]["act"][action]), self.tg))),
                (self.ty + self.tr + self.tg, (tl_id, None))
            ]:
                self.scheduler.push(*evt)

            self.set_phase(tl_id, self.get_next_yellow_phase_id(tl_id))
            self.set_phase_duration(tl_id, self.ty)

        while True:
            tl_evt = self.scheduler.pop()

            if tl_evt is None:
                self.simulation_step()

            else:
                tl_id, new_p = tl_evt

                if new_p is not None:
                    p, t = new_p
                    self.set_phase(tl_id, p)
                    self.set_phase_duration(tl_id, t)

                else:
                    self.next_tl_id = tl_id
                    return

    def obs(self):
        self.get_dtse(self.next_tl_id)
        return []

    def rew(self):
        tl_id = self.next_tl_id

        sum_delay = self.get_sum_delay(tl_id)

        self.rew_min = min([self.rew_min, -sum_delay])

        rew = 0 if self.rew_min == 0 else 1 + sum_delay / self.rew_min

        return rew

    def done(self):
        return self.is_simulation_end() or self.get_current_time() >= self.args["steps"]

    def info(self):
        return {}

    ####################################################################################################################
    ####################################################################################################################

    # Connected vehicles

    def get_con_p(self):
        return self.args["con_penetration_rate"]

    def get_veh_box(self):
        return self.args["v_min_gap"] + self.args["v_length"]

    def get_veh_max_speed(self):
        return self.args["v_max_speed"]

    def get_veh_con_range(self):
        return self.args["con_range"]

    def is_veh_con(self, veh_id):
        return self.get_veh_type(veh_id) == self.args["v_type_con"]



    def get_veh_con_on_edge(self, edge_id):
        return [veh_id for veh_id in self.get_edge_veh_ids(edge_id) if self.is_veh_con(veh_id)]

    def get_veh_delay(self, veh_id):
        return 1 - (self.get_veh_speed(veh_id) / self.get_veh_max_speed())

    def get_sum_delay(self, tl_id):
        sum_delay = 0

        for l in self.get_tl_incoming_lanes(tl_id):
            for v in self.get_lane_veh_ids(l):
                if self.get_veh_dist_from_junction(v) <= self.get_veh_con_range():
                    sum_delay += self.get_veh_delay(v)

        return sum_delay

    ####################################################################################################################
    ####################################################################################################################

    # DTSE

    def get_cell_length(self):
        return self.args["cell_length"]

    def get_n_cells(self):
        return self.args["con_range"] // self.args["cell_length"]

    def get_dtse_shape(self):
        return (
                self.get_n_cells() + 1,
                len(self.get_tl_incoming_lanes(self.tl_ids[0])),
                2
        )

    def get_dtse(self, tl_id):
        dtse = [[[
                    0 for _ in range(self.dtse_shape[0])
                ] for _ in range(self.dtse_shape[1])
            ] for _ in range(self.dtse_shape[2])
        ]

        for i, l in enumerate(self.get_tl_incoming_lanes(tl_id)):
            for v in self.get_lane_veh_ids(l):
                d = self.get_veh_dist_from_junction(v)
                if self.is_veh_con(v) and d <= self.get_veh_con_range():
                    dtse[0][i][int(d / self.get_cell_length())] = 1
                    dtse[1][i][int(d / self.get_cell_length())] = \
                        round(self.get_veh_speed(v) / self.get_veh_max_speed(), 2)  # + 0.001

        """"""
        [([print(b) for b in a], print("")) for a in dtse]

        [print(p, v) for p, v in zip(
            [item for sublist in dtse[0] for item in sublist],
            [item for sublist in dtse[1] for item in sublist]
        )]

        if random.uniform(0, 1) > 0.95:
            exit()
        """"""
