from .tl_scheduler import TlScheduler
from .sumo_env import SumoEnv

import random
from collections import deque


class RLController(SumoEnv):
    def __init__(self, *args, **kwargs):
        super(RLController, self).__init__(*args, **kwargs)

        self.tg = 10
        self.ty = 3
        self.tr = 2

        self.sum_delays = deque(maxlen=2)
        for _ in range(self.sum_delays.maxlen):
            self.sum_delays.append(1e-3)

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
        return []

    def rew(self):
        tl_id = self.next_tl_id

        self.sum_delays.append(self.get_sum_delay_veh_con(tl_id))

        rew = - (self.sum_delays[1] - self.sum_delays[0]) / self.sum_delays[0]

        rew = SumoEnv.clip(0, 1, rew + 0.5)

        print(rew)

        # rew2 = self.sum_delays[0] - self.sum_delays[1]
        # print(rew, rew2)

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

    """
    def get_sum_delay(self, tl_id):
        sum_delay = 1e-3

        for l in self.get_tl_incoming_lanes(tl_id):
            for v in self.get_lane_veh_ids(l):
                if self.get_veh_dist_from_junction(v) <= self.get_veh_con_range():
                    sum_delay += self.get_veh_delay(v)

        return sum_delay
    """

    def get_sum_delay_veh_con(self, tl_id):
        sum_delay = 1e-3

        for l in self.get_tl_incoming_lanes(tl_id):
            for v in self.get_lane_veh_ids(l):
                if self.is_veh_con(v) and self.get_veh_dist_from_junction(v) <= self.get_veh_con_range():
                    sum_delay += self.get_veh_delay(v)

        return sum_delay
