import torch.nn as nn
import torch.optim as optim

# """CHANGE HYPER PARAMETERS HERE""" ###################################################################################
HYPER_PARAMS = {
    'gpu': '0',                          # GPU #
    'n_env': 4,                          # Multi-processing environments
    'lr': 1e-04,                         # Learning rate
    'gamma': 0.99,                       # Discount factor
    'eps_start': 1.,                     # Epsilon start
    'eps_min': 0.01,                     # Epsilon min
    'eps_dec': 5e6,                      # Epsilon decay
    'eps_dec_exp': True,                 # Epsilon exponential decay
    'bs': 32,                            # Batch size
    'min_mem': 1000000,                  # Replay memory buffer min size
    'max_mem': 1000000,                  # Replay memory buffer max size
    'target_update_freq': 30000,         # Target network update frequency
    'target_soft_update': True,          # Target network soft update
    'target_soft_update_tau': 1e-03,     # Target network soft update tau rate
    'save_freq': 10000,                  # Save frequency
    'log_freq': 1000,                    # Log frequency
    'save_dir': './save/',               # Save directory
    'log_dir': './logs/train/',          # Log directory
    'load': True,                        # Load model
    'repeat': 5,                         # Repeat action
    'max_episode_steps': 5000,           # Time limit episode steps
    'max_total_steps': 0,                # Max total training steps if > 0, else inf training
    'algo': 'PerDuelingDoubleDQNAgent'   # DQNAgent
                                         # DoubleDQNAgent
                                         # DuelingDoubleDQNAgent
                                         # PerDuelingDoubleDQNAgent
}

########################################################################################################################


# """CHANGE NETWORK CONFIG HERE""" #####################################################################################
def network_config(input_dim):
    # """CHANGE NETWORK HERE""" ########################################################################################
    hidden_dims = (32, 32)

    activation = nn.ELU()

    net = nn.Sequential(
        nn.Linear(input_dim, hidden_dims[0]),
        activation,
        nn.Linear(hidden_dims[0], hidden_dims[1]),
        activation
    )
    ####################################################################################################################

    # """CHANGE OPTIMIZER HERE""" ######################################################################################
    optim_func = (lambda params, lr: optim.Adam(params, lr=lr))
    ####################################################################################################################

    # """CHANGE LOSS HERE""" ###########################################################################################
    loss_func = (lambda reduction: nn.SmoothL1Loss(reduction=reduction))
    ####################################################################################################################

    # """CHANGE FC DUELING LAYER OUTPUT DIM HERE""" ####################################################################
    fc_out_dim = hidden_dims[-1]
    ####################################################################################################################

    return net, optim_func, loss_func, fc_out_dim

########################################################################################################################
