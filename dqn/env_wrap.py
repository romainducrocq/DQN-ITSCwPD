import gym
from gym import spaces
import numpy as np

import os
from csv import DictWriter


class CustomEnvWrapper(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, custom_env):
        super(CustomEnvWrapper, self).__init__()

        self.custom_env = custom_env

        self.mode = self.custom_env.mode
        self.player = self.custom_env.player

        self.steps = 0
        self.total_reward = 0.

        action_space_n = self.custom_env.action_space_n
        observation_space_n = (self.custom_env.observation_space_n,) \
            if isinstance(self.custom_env.observation_space_n, int) else self.custom_env.observation_space_n

        self.action_space = spaces.Discrete(action_space_n)
        self.observation_space = spaces.Box(low=0., high=1., shape=observation_space_n, dtype=np.float32)

        self.log_info_buffer = []

    def get_env(self):
        return self.custom_env

    def _obs(self):
        obs = self.custom_env.obs()

        if isinstance(obs, np.ndarray):
            if obs.dtype == np.float32:
                return obs
            else:
                return obs.astype('float32')
        else:
            return np.array(obs, dtype=np.float32)

    def _rew(self):
        rew = self.custom_env.rew()

        self.total_reward += rew
        return rew

    def _done(self):
        return self.custom_env.done()

    def _info(self):
        info = {
            "l": self.steps,
            "r": self.total_reward
        }

        if not self.mode["train"]:
            info.update(self.custom_env.info())

        return info

    def reset(self):
        self.steps = 0
        self.total_reward = 0.

        self.custom_env.reset()

        if not self.mode["train"]:
            self.reset_render()

        return self._obs()

    def step(self, action):
        self.custom_env.step(action)

        if not self.mode["train"]:
            self.step_render()

        self.steps += 1

        return self._obs(), self._rew(), self._done(), self._info()

    def reset_render(self):
        self.custom_env.reset_render()

    def step_render(self):
        self.custom_env.step_render()

    def render(self, mode='human'):
        pass

    def log_info_writer(self, info, done, log, log_step, log_path):
        if log and (done or (log_step > 0 and info["l"] % log_step == 0)):
            if "TimeLimit.truncated" not in info:
                info["TimeLimit.truncated"] = False
            info["done"] = done

            self.log_info_buffer.append(info)

            if done:
                file_exists = os.path.isfile(log_path + ".csv")

                with open(log_path + ".csv", 'a') as f:
                    csv_writer = DictWriter(f, delimiter=',', lineterminator='\n', fieldnames=[k for k in info])
                    if not file_exists:
                        csv_writer.writeheader()
                    for log_info in self.log_info_buffer:
                        csv_writer.writerow(log_info)
                    f.close()

                self.log_info_buffer = []
