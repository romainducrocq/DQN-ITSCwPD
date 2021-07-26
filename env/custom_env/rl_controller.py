from .tl_scheduler import TlScheduler
from .sumo_env import SumoEnv

import random


class RLController(SumoEnv):
    def __init__(self, *args, **kwargs):
        super(RLController, self).__init__(*args, **kwargs)

        self.tg = 10
        self.ty = 3
        self.tr = 2

        self.dtse_shape = self.get_dtse_shape()
        # self.sum_delay_min = 0
        # self.sum_delay_min, self.sum_waiting_time_min = 0, 0
        self.sum_delay_sq_min = 0

        self.scheduler, self.next_tl_id = None, None

        self.action_space_n = len(self.tl_logic[self.tl_ids[0]]["act"])
        self.observation_space_n = self.dtse_shape

    def reset(self):
        self.simulation_reset()

        self.scheduler = TlScheduler(self.tg + self.ty + self.tr, self.tl_ids)
        self.next_tl_id = self.scheduler.pop()[0]

        for _ in range(self.tg):
            self.simulation_step()

    def step(self, action):
        # action = random.randint(0, self.action_space_n-1)

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
        tl_id = self.next_tl_id

        obs = self.get_dtse(tl_id)

        return obs

    def rew(self):
        tl_id = self.next_tl_id

        """
        sum_delay = self.get_sum_delay(tl_id)

        self.sum_delay_min = min([self.sum_delay_min, -sum_delay])

        rew = 0 if self.sum_delay_min == 0 else 1 + sum_delay / self.sum_delay_min
        """

        """
        sum_delay, sum_waiting_time = self.get_sum_delay_a_sum_waiting_time(tl_id)

        self.sum_delay_min, self.sum_waiting_time_min = \
            min([self.sum_delay_min, -sum_delay]), \
            min([self.sum_waiting_time_min, -sum_waiting_time])

        rew_delay, rew_waiting_time = \
            0 if self.sum_delay_min == 0 else 1 + sum_delay / self.sum_delay_min, \
            0 if self.sum_waiting_time_min == 0 else 1 + sum_waiting_time / self.sum_waiting_time_min

        w1, w2 = 0.5, 0.5
        
        rew = w1 * rew_delay + w2 * rew_waiting_time
        """

        """"""
        sum_delay_sq = self.get_sum_delay_sq(tl_id)

        self.sum_delay_sq_min = min([self.sum_delay_sq_min, -sum_delay_sq])

        rew = 0 if self.sum_delay_sq_min == 0 else 1 + sum_delay_sq / self.sum_delay_sq_min
        """"""

        rew = SumoEnv.clip(0, 1, rew)

        return rew

    def done(self):
        return self.is_simulation_end() or self.get_current_time() >= self.args["steps"]

    ####################################################################################################################
    ####################################################################################################################

    # Connected vehicles

    def get_veh_delay_sq(self, veh_id):
        return 1 - pow((self.get_veh_speed(veh_id) / self.args["v_max_speed"]), 2)

    def get_sum_delay_sq(self, tl_id):
        sum_delay = 0

        for veh_id in self.yield_tl_vehs(tl_id):
            sum_delay += self.get_veh_delay_sq(veh_id)

        return sum_delay

    """
    def get_veh_delay(self, veh_id):
        return 1 - (self.get_veh_speed(veh_id) / self.args["v_max_speed"])
    """

    """
    def get_sum_delay(self, tl_id):
        sum_delay = 0

        for veh_id in self.yield_tl_vehs(tl_id):
            sum_delay += self.get_veh_delay(veh_id)

        return sum_delay
    """

    """
    def get_sum_waiting_time(self, tl_id):
        sum_waiting_time = 0

        for veh_id in self.yield_tl_vehs(tl_id):
            sum_waiting_time += self.get_veh_waiting_time(veh_id)

        return sum_waiting_time
    """

    """
    def get_sum_delay_a_sum_waiting_time(self, tl_id):
        sum_delay, sum_waiting_time = 0, 0

        for veh_id in self.yield_tl_vehs(tl_id):
            sum_delay += self.get_veh_delay(veh_id)
            sum_waiting_time += self.get_veh_waiting_time(veh_id)

        return sum_delay, sum_waiting_time
    """

    def get_n_cells(self):
        return self.args["con_range"] // self.args["cell_length"]

    def get_dtse_shape(self):
        return (
            3,
            len(self.get_tl_incoming_lanes(self.tl_ids[0])),
            self.get_n_cells()
        )

    def get_dtse(self, tl_id):
        dtse = [[[
                    0. for _ in range(self.dtse_shape[2])
                ] for _ in range(self.dtse_shape[1])
            ] for _ in range(self.dtse_shape[0])
        ]

        for l, lane_id in enumerate(self.get_tl_incoming_lanes(tl_id)):
            for veh_id in self.get_lane_veh_ids(lane_id):
                dist = self.get_veh_dist_from_junction(veh_id)
                if self.is_veh_con(veh_id) and dist <= self.args["con_range"]:
                    dtse[0][l][int(dist / self.args["cell_length"])] = 1.
                    dtse[1][l][int(dist / self.args["cell_length"])] = \
                        self.get_veh_speed(veh_id) / self.args["v_max_speed"]
                    # round(self.get_veh_speed(veh_id) / self.args["v_max_speed"], 2)

            if self.is_tl_lane_signal_green(tl_id, lane_id):
                dtse[2][l] = [1. for _ in range(self.dtse_shape[2])]

        # self.print_dtse(dtse)

        return dtse

    def print_dtse(self, dtse):
        """"""
        print(self.dtse_shape)
        [([print(h) for h in c], print("")) for c in dtse]

        # exit()
        """"""

        """
        [print(p, v, s) for p, v, s in zip(
            [item for sublist in dtse[0] for item in sublist],
            [item for sublist in dtse[1] for item in sublist],
            [item for sublist in dtse[2] for item in sublist]
        )]

        # exit()
        """
