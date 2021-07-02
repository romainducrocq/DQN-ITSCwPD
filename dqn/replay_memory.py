from .utils import ABCMeta, abstract_attribute, SumTree

import random
import numpy as np
from collections import deque


class ReplayMemory(metaclass=ABCMeta):
    def __init__(self, buffer_size, batch_size):
        self.batch_size = batch_size
        self.buffer_size = buffer_size

    @abstract_attribute
    def replay_buffer(self):
        pass

    def store_transitions(self, obses, actions, rews, dones, new_obses):
        raise NotImplementedError

    def sample_transitions(self, step):
        raise NotImplementedError


class ReplayMemoryNaive(ReplayMemory):
    def __init__(self, *args, **kwargs):
        super(ReplayMemoryNaive, self).__init__(*args, **kwargs)

        self.replay_buffer = deque(maxlen=self.buffer_size)

    def store_transitions(self, obses, actions, rews, dones, new_obses):
        for e, (obs, action, rew, done, new_obs) in enumerate(zip(obses, actions, rews, dones, new_obses)):
            transition = (obs, action, rew, done, new_obs)
            self.replay_buffer.append(transition)

            if done:
                yield e

    def sample_transitions(self, step=None):
        return random.sample(self.replay_buffer, self.batch_size)


# https://danieltakeshi.github.io/2019/07/14/per/
class ReplayMemoryPrioritized(ReplayMemory):
    def __init__(self, buffer_size, batch_size, eps_dec):
        super(ReplayMemoryPrioritized, self).__init__(buffer_size, batch_size)

        self.replay_buffer = SumTree(self.buffer_size)

        self.epsilon = 0.0001
        self.alpha = 0.6
        self.beta_start = 0.4
        self.beta_end = 1.
        self.beta_inc = eps_dec
        self.max_priority_high = 1.

    def store_transitions(self, obses, actions, rews, dones, new_obses):
        max_priority = self.replay_buffer.max_priority

        if max_priority == 0:
            max_priority = self.max_priority_high

        for e, (obs, action, rew, done, new_obs) in enumerate(zip(obses, actions, rews, dones, new_obses)):
            transition = (obs, action, rew, done, new_obs)
            self.replay_buffer.add(max_priority, transition)

            if done:
                yield e

    def sample_transitions(self, step):
        is_weights, tree_indices, transitions = [], [], []

        priority_segment = self.replay_buffer.total_priority / self.batch_size

        beta = np.interp(step, [0, self.beta_inc], [self.beta_start, self.beta_end])

        prob_min = self.replay_buffer.min_priority / self.replay_buffer.total_priority
        max_is_weight = pow(self.replay_buffer.size * prob_min, -beta)

        for i in range(self.batch_size):
            v = np.random.uniform(priority_segment * i, priority_segment * (i + 1))

            tree_index, priority, transition = self.replay_buffer.get_leaf(v)

            prob_i = priority / self.replay_buffer.total_priority

            is_weight_i = pow(self.replay_buffer.size * prob_i, -beta) / max_is_weight

            is_weights.append(is_weight_i)
            tree_indices.append(tree_index)
            transitions.append(transition)

        return is_weights, tree_indices, transitions

    def update_batch_priorities(self, tree_indices, abs_td_errors_np):
        priorities = list(np.power(np.minimum(abs_td_errors_np + self.epsilon, self.max_priority_high), self.alpha))

        for i, p in zip(tree_indices, priorities):
            self.replay_buffer.update(i, p)
