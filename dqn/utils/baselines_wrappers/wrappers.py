import gym


class RepeatActionWrapper(gym.Wrapper):
    def __init__(self, env, repeat=4):
        """Return only every `repeat`-th frame"""
        super(RepeatActionWrapper, self).__init__(env)
        self._repeat = repeat

    def step(self, action):
        """Repeat action, sum reward over last observations."""
        total_reward = 0.0
        done = False
        for i in range(self._repeat):
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            if done:
                break

        return obs, total_reward, done, info

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)


class MaxEpisodeStepsWrapper(gym.Wrapper):
    def __init__(self, env, max_episode_steps=None):
        super(MaxEpisodeStepsWrapper, self).__init__(env)
        self._max_episode_steps = max_episode_steps
        self._elapsed_steps = 0

    def step(self, ac):
        observation, reward, done, info = self.env.step(ac)
        self._elapsed_steps += 1
        if self._elapsed_steps >= self._max_episode_steps:
            done = True
            info['TimeLimit.truncated'] = True
        return observation, reward, done, info

    def reset(self, **kwargs):
        self._elapsed_steps = 0
        return self.env.reset(**kwargs)
