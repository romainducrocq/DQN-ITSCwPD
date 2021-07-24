from .dqn_config import HYPER_PARAMS, network_config
from .dqn_env import DqnEnv as CustomEnv
from .view import PYGLET
if PYGLET:
    from .view import PygletView as View
else:
    from .view import CustomView as View


__all__ = ['HYPER_PARAMS', 'network_config', 'CustomEnv', 'View']
