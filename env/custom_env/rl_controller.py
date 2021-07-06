from .tl_scheduler import TlScheduler
from .sumo_env import SumoEnv

import random


class RLController(SumoEnv):
    def __init__(self, *args, **kwargs):
        super(RLController, self).__init__(*args, **kwargs)

        self.tg = 10
        self.ty = 3
        self.tr = 2

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

        sum_delay, max_n_veh = 0, 0

        for (l, get_veh_dist) in (
                [(l, self.get_veh_dist_from_junction) for l in self.get_tl_incoming_lanes(tl_id)] +
                [(l, self.get_veh_pos_on_lane) for l in self.get_tl_outgoing_lanes(tl_id)]
        ):
            max_n_veh += int(min(self.get_veh_con_range(), self.get_lane_length(l)) / self.get_veh_box())

            for v in self.get_lane_veh_ids(l):
                if self.is_veh_con(v) and get_veh_dist(v) <= self.get_veh_con_range():
                    sum_delay += self.get_veh_delay_norm(v)

        rew = 1 - SumoEnv.clip(0, 1, sum_delay / (max_n_veh * self.get_con_p()))

        print(rew)
        return rew

    def done(self):
        return self.is_simulation_end() or self.get_current_time() >= self.args["steps"]

    def info(self):
        return {}
