from .utils.baselines_wrappers import DummyVecEnv, SubprocVecEnv, Monitor, RepeatActionWrapper, MaxEpisodeStepsWrapper


def wrap_repeat_action(env, repeat):
    return RepeatActionWrapper(env, repeat=repeat)


def wrap_max_episode_steps(env, max_episode_steps):
    return MaxEpisodeStepsWrapper(env, max_episode_steps=max_episode_steps)


def make_vec_env(env, n_env):
    if n_env > 1:
        return SubprocVecEnv([lambda: Monitor(env, allow_early_resets=True) for _ in range(n_env)])
    else:
        return DummyVecEnv([lambda: Monitor(env, allow_early_resets=True) for _ in range(n_env)])


def make_env(env, repeat=0, max_episode_steps=0, n_env=0):
    if repeat > 0:
        env = wrap_repeat_action(env, repeat)

    if max_episode_steps > 0:
        env = wrap_max_episode_steps(env, max_episode_steps)

    if n_env == 0:
        return env

    return make_vec_env(env, n_env)
