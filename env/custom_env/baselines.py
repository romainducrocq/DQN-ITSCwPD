from .utils import \
    pretty_print, \
    arg_max

from .tl_scheduler import TlScheduler
from .sumo_env import SumoEnv


class BaselineMeta(SumoEnv):
    def __init__(self, *args, **kwargs):
        super(BaselineMeta, self).__init__(*args, **kwargs)

    def reset(self):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError

    def obs(self):
        return []

    def rew(self):
        return 0

    def done(self):
        return SumoEnv.is_simulation_end() or SumoEnv.get_current_time() >= self.steps

    def info(self):
        raise NotImplementedError


class UniformBaseline(BaselineMeta):
    def __init__(self, *args, **kwargs):
        super(UniformBaseline, self).__init__(*args, **kwargs)

    def reset(self):
        self.simulation_reset()

    def step(self):
        SumoEnv.simulation_step()

    def info(self):
        return {}


class MaxPressureBaseline(BaselineMeta):
    def __init__(self, *args, **kwargs):
        super(MaxPressureBaseline, self).__init__(*args, **kwargs)

        self.tg = 10
        self.ty = 3

        self.scheduler = TlScheduler(self.tg, self.tl_ids)

    @staticmethod
    def pressure(li, lo):
        return sum([SumoEnv.get_lane_veh_n(l) for l in li]) - sum([SumoEnv.get_lane_veh_n(l) for l in lo])

    def max_pressure(self, tl_id):
        return self.tl_logic[tl_id]["act"][arg_max([
            MaxPressureBaseline.pressure(
                self.tl_logic[tl_id]["map"][a]["li"],
                self.tl_logic[tl_id]["map"][a]["lo"]
            ) for a in self.tl_logic[tl_id]["act"]
        ])]

    def reset(self):
        self.simulation_reset()

    def step(self):
        while True:
            tl_evt = self.scheduler.pop()
            if tl_evt is not None:
                break
            SumoEnv.simulation_step()

        tl_id, new_p = tl_evt

        if new_p is None:
            max_p = self.max_pressure(tl_id)

            if max_p == SumoEnv.get_ryg_state(tl_id):
                t = self.tg

            else:
                SumoEnv.set_phase(tl_id, self.get_next_yellow_phase_id(tl_id))
                t, new_p = self.ty, max_p

        else:
            SumoEnv.set_phase(tl_id, self.get_new_green_phase_id(tl_id, new_p))
            t, new_p = self.tg, None

        SumoEnv.set_phase_duration(tl_id, t)
        self.scheduler.push(t, (tl_id, new_p))

    def info(self):
        return {}


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

        self.scheduler = TlScheduler(self.tg, self.tl_ids)

    def reset(self):
        self.simulation_reset()

    def step(self):
        while True:
            tl_evt = self.scheduler.pop()
            if tl_evt is not None:
                break
            SumoEnv.simulation_step()

            for tl_id in self.tl_ids:
                for l in self.get_red_tl_incoming_lanes(tl_id):
                    self.kappa[tl_id] += SumoEnv.get_lane_veh_n_in_dist(l, self.r_dist)

        tl_id, new_p = tl_evt

        if new_p is None:
            n = sum([self.get_lane_veh_n_in_dist(l, self.g_dist) for l in self.get_green_tl_incoming_lanes(tl_id)])

            if 0 < n <= self.mu or self.kappa[tl_id] <= self.theta:
                t = 1

            else:
                t, new_p = self.ty, self.get_next_green_phase_ryg_state(tl_id)
                SumoEnv.set_phase(tl_id, self.get_next_yellow_phase_id(tl_id))

        else:
            SumoEnv.set_phase(tl_id, self.get_new_green_phase_id(tl_id, new_p))
            t, new_p = self.tg, None

            self.kappa[tl_id] = 0

        SumoEnv.set_phase_duration(tl_id, t)
        self.scheduler.push(t, (tl_id, new_p))

    def info(self):
        return {}
