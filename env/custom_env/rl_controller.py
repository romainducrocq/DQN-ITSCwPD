from .utils import \
    pretty_print

from .tl_scheduler import TlScheduler
from .sumo_env import SumoEnv


class RLController(SumoEnv):
    def __init__(self, *args, **kwargs):
        super(RLController, self).__init__(*args, **kwargs)

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

    def info(self):
        raise NotImplementedError
