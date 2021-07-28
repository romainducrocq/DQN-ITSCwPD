from .tl_scheduler import TlScheduler
from .sumo_env import SumoEnv


class BaselineMeta(SumoEnv):
    def __init__(self, *args, **kwargs):
        super(BaselineMeta, self).__init__(*args, **kwargs)

        self.action_space_n = 1
        self.observation_space_n = 1

    def reset(self):
        raise NotImplementedError

    def step(self, action):
        raise NotImplementedError

    def obs(self):
        return []

    def rew(self):
        return 0

    def done(self):
        return self.is_simulation_end() or self.get_current_time() >= self.args["steps"]


class UniformBaseline(BaselineMeta):
    def __init__(self, *args, **kwargs):
        super(UniformBaseline, self).__init__(*args, **kwargs)

        self.tg = 10
        self.ty = 3
        self.tr = 2

        self.scheduler, self.next_tl_id = None, None

    def reset(self):
        self.simulation_reset()

        self.scheduler = TlScheduler(self.tg + self.ty + self.tr, self.tl_ids)
        self.next_tl_id = self.scheduler.pop()[0]

        for _ in range(self.tg):
            self.simulation_step()

    def step(self, action):
        tl_id = self.next_tl_id

        for evt in [
            (self.ty, (tl_id, (self.get_next_red_phase_id(tl_id), self.tr))),
            (self.ty + self.tr,
             (tl_id, (self.get_new_green_phase_id(tl_id, self.get_next_green_phase_ryg_state(tl_id)), self.tg))),
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


class MaxPressureBaseline(BaselineMeta):
    def __init__(self, *args, **kwargs):
        super(MaxPressureBaseline, self).__init__(*args, **kwargs)

        self.tg = 10
        self.ty = 3
        self.tr = 2

        self.scheduler, self.next_tl_id = None, None

    def pressure(self, li, lo):
        # return sum([self.get_lane_veh_n(l) for l in li]) - sum([self.get_lane_veh_n(l) for l in lo])
        return sum([self.get_lane_veh_con_n_in_dist_in(l, self.args["con_range"]) for l in li]) \
               - sum([self.get_lane_veh_con_n_in_dist_out(l, self.args["con_range"]) for l in lo])

    def max_pressure(self, tl_id):
        return self.tl_logic[tl_id]["act"][SumoEnv.arg_max([
            self.pressure(
                self.tl_logic[tl_id]["map"][a]["li"],
                self.tl_logic[tl_id]["map"][a]["lo"]
            ) for a in self.tl_logic[tl_id]["act"]
        ])]

    def reset(self):
        self.simulation_reset()

        self.scheduler = TlScheduler(self.tg + self.ty + self.tr, self.tl_ids)
        self.next_tl_id = self.scheduler.pop()[0]

        for _ in range(self.tg):
            self.simulation_step()

    def step(self, action):
        tl_id = self.next_tl_id

        max_p = self.max_pressure(tl_id)

        if max_p == self.get_ryg_state(tl_id):
            self.scheduler.push(self.tg, (tl_id, None))
            self.set_phase_duration(tl_id, self.tg)

        else:
            for evt in [
                (self.ty, (tl_id, (self.get_next_red_phase_id(tl_id), self.tr))),
                (self.ty + self.tr, (tl_id, (self.get_new_green_phase_id(tl_id, max_p), self.tg))),
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

    ####################################################################################################################
    ####################################################################################################################

    # Connected vehicles

    def get_lane_veh_con_n_in_dist_in(self, lane_id, dist):
        return sum(
            [1 for veh_id in self.get_lane_veh_ids(lane_id)
             if self.is_veh_con(veh_id) and (self.get_lane_length(lane_id) - self.get_veh_pos_on_lane(veh_id)) <= dist]
        )

    def get_lane_veh_con_n_in_dist_out(self, lane_id, dist):
        return sum(
            [1 for veh_id in self.get_lane_veh_ids(lane_id)
             if self.is_veh_con(veh_id) and self.get_veh_pos_on_lane(veh_id) <= dist]
        )

    def get_lane_veh_con_n(self, lane_id):
        return sum([1 for veh_id in self.get_lane_veh_ids(lane_id) if self.is_veh_con(veh_id)])


class SotlBaseline(BaselineMeta):
    def __init__(self, *args, **kwargs):
        super(SotlBaseline, self).__init__(*args, **kwargs)

        # https://arxiv.org/pdf/1406.1128.pdf
        self.kappa = {tl_id: 0 for tl_id in self.tl_ids}
        self.theta = 50
        self.r_dist = 80
        self.g_dist = 25
        self.mu = 3

        self.tg = 10
        self.ty = 3
        self.tr = 2

        self.scheduler, self.next_tl_id = None, None

    def reset(self):
        self.simulation_reset()

        self.scheduler = TlScheduler(self.tg + self.ty + self.tr, self.tl_ids)
        self.next_tl_id = self.scheduler.pop()[0]

        for _ in range(self.tg):
            self.simulation_step()

            for tl_id in self.tl_ids:
                for l in self.get_red_tl_incoming_lanes(tl_id):
                    # self.kappa[tl_id] += self.get_lane_veh_n_in_dist(l, self.r_dist)
                    self.kappa[tl_id] += self.get_lane_veh_con_n_in_dist(l, self.r_dist)

    def step(self, action):
        tl_id = self.next_tl_id

        # n = sum([self.get_lane_veh_n_in_dist(l, self.g_dist) for l in self.get_green_tl_incoming_lanes(tl_id)])
        n = sum([self.get_lane_veh_con_n_in_dist(l, self.g_dist) for l in self.get_green_tl_incoming_lanes(tl_id)])

        if 0 < n <= self.mu or self.kappa[tl_id] <= self.theta:
            self.scheduler.push(self.tg, (tl_id, None))
            self.set_phase_duration(tl_id, 1)

        else:
            for evt in [
                (self.ty, (tl_id, (self.get_next_red_phase_id(tl_id), self.tr))),
                (self.ty + self.tr,
                 (tl_id, (self.get_new_green_phase_id(tl_id, self.get_next_green_phase_ryg_state(tl_id)), self.tg))),
                (self.ty + self.tr + self.tg, (tl_id, None))
            ]:
                self.scheduler.push(*evt)

            self.set_phase(tl_id, self.get_next_yellow_phase_id(tl_id))
            self.set_phase_duration(tl_id, self.ty)

        while True:
            tl_evt = self.scheduler.pop()

            if tl_evt is None:
                self.simulation_step()

                for tl_id in self.tl_ids:
                    for l in self.get_red_tl_incoming_lanes(tl_id):
                        # self.kappa[tl_id] += self.get_lane_veh_n_in_dist(l, self.r_dist)
                        self.kappa[tl_id] += self.get_lane_veh_con_n_in_dist(l, self.r_dist)

            else:
                tl_id, new_p = tl_evt

                if new_p is not None:
                    p, t = new_p
                    self.set_phase(tl_id, p)
                    self.set_phase_duration(tl_id, t)

                    self.kappa[tl_id] = 0

                else:
                    self.next_tl_id = tl_id
                    return

    ####################################################################################################################
    ####################################################################################################################

    # Connected vehicles

    def get_lane_veh_con_n_in_dist(self, lane_id, dist):
        return sum(
            [1 for veh_id in self.get_lane_veh_ids(lane_id)
             if self.is_veh_con(veh_id) and (self.get_lane_length(lane_id) - self.get_veh_pos_on_lane(veh_id)) <= dist]
        )
