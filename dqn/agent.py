from .utils import ABCMeta, abstract_attribute
from .replay_memory import ReplayMemoryNaive, ReplayMemoryPrioritized
from .network import DeepQNetwork, DuelingDeepQNetwork

import os
import time
import math
import random
import numpy as np
from collections import deque
from datetime import timedelta

import torch as T
from torch.utils.tensorboard import SummaryWriter


class Agent(metaclass=ABCMeta):
    def __init__(self, n_env, lr, gamma, epsilon_start, epsilon_min, epsilon_decay, epsilon_exp_decay, nn_conf_func, input_dim, output_dim,
                 batch_size, min_buffer_size, buffer_size, update_target_frequency, target_soft_update, target_soft_update_tau,
                 save_frequency, log_frequency, save_dir, log_dir, load, algo, gpu):
        self.n_env = n_env
        self.lr = lr
        self.gamma = gamma
        self.epsilon_start = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.epsilon_exp_decay = epsilon_exp_decay
        self.nn_conf_func = nn_conf_func
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.batch_size = batch_size
        self.min_buffer_size = min_buffer_size
        self.buffer_size = buffer_size
        self.update_target_frequency = update_target_frequency
        self.target_soft_update = target_soft_update
        self.target_soft_update_tau = target_soft_update_tau
        self.save_frequency = save_frequency
        self.log_frequency = log_frequency
        self.load = load

        self.step = 0
        self.resume_step = 0
        self.episode_count = 0
        self.ep_info_buffer = deque([], maxlen=100)

        path = algo + '_lr' + str(lr)
        self.save_path = save_dir + path + '_' + 'model.pack'
        self.summary_writer = SummaryWriter(log_dir + path + '/')

        self.device = T.device(("cuda:"+gpu) if T.cuda.is_available() else "cpu")
        print("DEVICE", "=", self.device, "" if not T.cuda.is_available() else T.cuda.get_device_name(self.device))

        self.start_time = time.time()

    @abstract_attribute
    def replay_memory_buffer(self):
        pass

    @abstract_attribute
    def online_network(self):
        pass

    @abstract_attribute
    def target_network(self):
        pass

    def learn(self):
        raise NotImplementedError

    def transitions_to_tensor(self, transitions):
        obses_t = T.as_tensor(np.asarray([t[0] for t in transitions]), dtype=T.float32).to(self.device)
        actions_t = T.as_tensor(np.asarray([t[1] for t in transitions]), dtype=T.int64).to(self.device).unsqueeze(-1)
        rews_t = T.as_tensor(np.asarray([t[2] for t in transitions]), dtype=T.float32).to(self.device).unsqueeze(-1)
        dones_t = T.as_tensor(np.asarray([t[3] for t in transitions]), dtype=T.float32).to(self.device).unsqueeze(-1)
        new_obses_t = T.as_tensor(np.asarray([t[4] for t in transitions]), dtype=T.float32).to(self.device)

        return obses_t, actions_t, rews_t, dones_t, new_obses_t

    def store_transitions(self, obses, actions, rews, dones, new_obses, infos):
        for i in self.replay_memory_buffer.store_transitions(obses, actions, rews, dones, new_obses):
            if infos:
                self.ep_info_buffer.append({'r': infos[i]['r'], 'l': infos[i]['l']})
                self.episode_count += 1

    def epsilon(self):
        if self.epsilon_exp_decay:
            return np.exp(np.interp(self.step * self.n_env, [0, self.epsilon_decay], [np.log(self.epsilon_start), np.log(self.epsilon_min)]))
        else:
            return np.interp(self.step * self.n_env, [0, self.epsilon_decay], [self.epsilon_start, self.epsilon_min])

    def choose_actions(self, obses):
        actions = self.online_network.actions(obses)

        for i in range(len(actions)):
            if random.random() <= self.epsilon():
                actions[i] = random.randint(0, self.output_dim - 1)

        return actions

    def update_target_network(self, force=False):
        if (not self.target_soft_update and self.step % (self.update_target_frequency // self.n_env) == 0) or force:
            self.target_network.load_state_dict(self.online_network.state_dict())

        elif self.target_soft_update:
            for target_network_param, online_network_param in zip(self.target_network.parameters(), self.online_network.parameters()):
                target_network_param.data.copy_(
                    (self.target_soft_update_tau * self.n_env) * online_network_param.data +
                    (1. - (self.target_soft_update_tau * self.n_env)) * target_network_param.data
                )

    def load_model(self):
        if self.load and os.path.exists(self.save_path):
            print()
            print("Resume training from " + self.save_path + "...")
            self.resume_step, self.episode_count, rew_mean, len_mean = self.online_network.load(self.save_path)
            [self.ep_info_buffer.append({'r': rew_mean, 'l': len_mean}) for _ in range(np.min([self.episode_count, self.ep_info_buffer.maxlen]))]
            print("Step: ", self.resume_step * self.n_env, ", Episodes: ", self.episode_count, ", Avg Rew: ", rew_mean, ", Avg Ep Len: ", len_mean)

            self.update_target_network(force=True)
            self.step = self.resume_step

    def save_model(self):
        if self.step % self.save_frequency == 0 and self.step > self.resume_step:
            print()
            print("Saving model...")
            self.online_network.save(self.save_path, self.step, self.episode_count, self.info_mean('r'), self.info_mean('l'))
            print("OK!")

    def log(self):
        if self.step % self.log_frequency == 0 and self.step > self.resume_step:
            rew_mean, len_mean = self.info_mean('r'), self.info_mean('l')

            print()
            print('Step: ', self.step * self.n_env, ' (' + str(self.step) + 'x' + str(self.n_env) + ')')
            print('Avg Rew: ', rew_mean)
            print('Avg Ep Len: ', len_mean)
            print('Episodes: ', self.episode_count)
            print('---', str(timedelta(seconds=round((time.time() - self.start_time), 0))), '---')

            self.summary_writer.add_scalar('AvgRew', rew_mean, global_step=(self.step * self.n_env))
            self.summary_writer.add_scalar('AvgEpLen', len_mean, global_step=(self.step * self.n_env))
            self.summary_writer.add_scalar('Episodes', self.episode_count, global_step=(self.step * self.n_env))

    def info_mean(self, i):
        i_mean = np.mean([e[i] for e in self.ep_info_buffer])
        return i_mean if not math.isnan(i_mean) else 0.


class SimpleAgent(Agent):
    def __init__(self, *args, **kwargs):
        super(SimpleAgent, self).__init__(*args, **kwargs)

    @abstract_attribute
    def replay_memory_buffer(self):
        pass

    @abstract_attribute
    def online_network(self):
        pass

    @abstract_attribute
    def target_network(self):
        pass

    def learn(self):
        # Compute loss
        transitions = self.replay_memory_buffer.sample_transitions()
        obses_t, actions_t, rews_t, dones_t, new_obses_t = self.transitions_to_tensor(transitions)

        with T.no_grad():
            target_q_values = self.target_network(new_obses_t)
            max_target_q_values = target_q_values.max(dim=1, keepdim=True)[0]

            targets = rews_t + (1 - dones_t) * self.gamma * max_target_q_values

        online_q_values = self.online_network(obses_t)
        action_q_values = T.gather(input=online_q_values, dim=1, index=actions_t)

        loss = self.online_network.loss(action_q_values, targets).to(self.device)

        # Gradient descent
        self.online_network.optimizer.zero_grad()
        loss.backward()
        self.online_network.optimizer.step()


class DoubleAgent(Agent):
    def __init__(self, *args, **kwargs):
        super(DoubleAgent, self).__init__(*args, **kwargs)

    @abstract_attribute
    def replay_memory_buffer(self):
        pass

    @abstract_attribute
    def online_network(self):
        pass

    @abstract_attribute
    def target_network(self):
        pass

    def learn(self):
        # Compute loss
        transitions = self.replay_memory_buffer.sample_transitions()
        obses_t, actions_t, rews_t, dones_t, new_obses_t = self.transitions_to_tensor(transitions)

        with T.no_grad():
            targets_online_q_values = self.online_network(new_obses_t)
            targets_online_best_q_indices = targets_online_q_values.argmax(dim=1, keepdim=True)

            targets_target_q_values = self.target_network(new_obses_t)
            targets_selected_q_values = T.gather(input=targets_target_q_values, dim=1, index=targets_online_best_q_indices)

            targets = rews_t + (1 - dones_t) * self.gamma * targets_selected_q_values

        online_q_values = self.online_network(obses_t)
        action_q_values = T.gather(input=online_q_values, dim=1, index=actions_t)

        loss = self.online_network.loss(action_q_values, targets).to(self.device)

        # Gradient descent
        self.online_network.optimizer.zero_grad()
        loss.backward()
        self.online_network.optimizer.step()


class PerDoubleAgent(Agent):
    def __init__(self, *args, **kwargs):
        super(PerDoubleAgent, self).__init__(*args, **kwargs)

    @abstract_attribute
    def replay_memory_buffer(self):
        pass

    @abstract_attribute
    def online_network(self):
        pass

    @abstract_attribute
    def target_network(self):
        pass

    def learn(self):
        # Compute loss
        is_weights, tree_indices, transitions = self.replay_memory_buffer.sample_transitions(self.step * self.n_env)
        is_weights_t = T.as_tensor(np.asarray(is_weights), dtype=T.float32).to(self.device).unsqueeze(-1)
        obses_t, actions_t, rews_t, dones_t, new_obses_t = self.transitions_to_tensor(transitions)

        with T.no_grad():
            targets_online_q_values = self.online_network(new_obses_t)
            targets_online_best_q_indices = targets_online_q_values.argmax(dim=1, keepdim=True)

            targets_target_q_values = self.target_network(new_obses_t)
            targets_selected_q_values = T.gather(input=targets_target_q_values, dim=1, index=targets_online_best_q_indices)

            targets = rews_t + (1 - dones_t) * self.gamma * targets_selected_q_values

        online_q_values = self.online_network(obses_t)
        action_q_values = T.gather(input=online_q_values, dim=1, index=actions_t)

        with T.no_grad():
            abs_td_errors_np = T.abs(targets - action_q_values).detach().cpu().numpy()
            self.replay_memory_buffer.update_batch_priorities(tree_indices, abs_td_errors_np)

        loss = T.mean(is_weights_t * self.online_network.loss(action_q_values, targets)).to(self.device)

        # Gradient descent
        self.online_network.optimizer.zero_grad()
        loss.backward()
        self.online_network.optimizer.step()


class DQNAgent(SimpleAgent):
    def __init__(self, *args, **kwargs):
        super(DQNAgent, self).__init__(*args, **kwargs)

        self.replay_memory_buffer = ReplayMemoryNaive(self.buffer_size, self.batch_size)

        self.online_network = DeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim)
        self.target_network = DeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim)

        self.update_target_network(force=True)


class DoubleDQNAgent(DoubleAgent):
    def __init__(self, *args, **kwargs):
        super(DoubleDQNAgent, self).__init__(*args, **kwargs)

        self.replay_memory_buffer = ReplayMemoryNaive(self.buffer_size, self.batch_size)

        self.online_network = DeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim)
        self.target_network = DeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim)

        self.update_target_network(force=True)


class DuelingDoubleDQNAgent(DoubleAgent):
    def __init__(self, *args, **kwargs):
        super(DuelingDoubleDQNAgent, self).__init__(*args, **kwargs)

        self.replay_memory_buffer = ReplayMemoryNaive(self.buffer_size, self.batch_size)

        self.online_network = DuelingDeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim)
        self.target_network = DuelingDeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim)

        self.update_target_network(force=True)


class PerDuelingDoubleDQNAgent(PerDoubleAgent):
    def __init__(self, *args, **kwargs):
        super(PerDuelingDoubleDQNAgent, self).__init__(*args, **kwargs)

        self.replay_memory_buffer = ReplayMemoryPrioritized(self.buffer_size, self.batch_size, self.epsilon_decay)

        self.online_network = DuelingDeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim, reduction='none')
        self.target_network = DuelingDeepQNetwork(self.device, self.lr, self.nn_conf_func, self.input_dim, self.output_dim, reduction='none')

        self.update_target_network(force=True)
