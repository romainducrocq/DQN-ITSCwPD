# """CHANGE CUSTOM ENV IMPORT HERE""" ##################################################################################
from .custom_env import SUMO_PARAMS, Baselines, RLController
########################################################################################################################


class DqnEnv:

    def min_max_scale(self, x, feature):
        return (x - self.min_max[feature][0]) / (self.min_max[feature][1] - self.min_max[feature][0])

    def __init__(self, m, p=None):
        self.mode = {"train": False, "observe": False, "play": False, m: True}
        self.player = p if self.mode["play"] else None

        # """CHANGE ENV CONSTRUCT HERE""" ##############################################################################
        if self.mode["train"]:
            self.sumo_env = RLController(gui=False, log=False, rnd=(True, True))
        elif self.mode["observe"]:
            self.sumo_env = RLController(gui=SUMO_PARAMS["gui"], log=SUMO_PARAMS["log"], rnd=SUMO_PARAMS["rnd"])
        elif self.mode["play"]:
            if p == "Test":
                self.sumo_env = RLController(gui=SUMO_PARAMS["gui"], log=SUMO_PARAMS["log"], rnd=SUMO_PARAMS["rnd"])
            else:
                self.sumo_env = getattr(Baselines, p)(gui=SUMO_PARAMS["gui"], log=SUMO_PARAMS["log"], rnd=SUMO_PARAMS["rnd"])
        ################################################################################################################

        # """CHANGE FEATURE SCALING HERE""" ############################################################################
        self.min_max = {
        }
        ################################################################################################################

        # """CHANGE ACTION AND OBSERVATION SPACE SIZES HERE""" #########################################################
        self.action_space_n = self.sumo_env.action_space_n
        self.observation_space_n = self.sumo_env.observation_space_n
        ################################################################################################################

    def obs(self):
        # """CHANGE OBSERVATION HERE""" ################################################################################
        obs = self.sumo_env.obs()
        ################################################################################################################
        return obs

    def rew(self):
        # """CHANGE REWARD HERE""" #####################################################################################
        rew = self.sumo_env.rew()
        ################################################################################################################
        return rew

    def done(self):
        # """CHANGE DONE HERE""" #######################################################################################
        done = self.sumo_env.done()
        ################################################################################################################
        return done

    def info(self):
        # """CHANGE INFO HERE""" #######################################################################################
        info = self.sumo_env.info()
        ################################################################################################################
        return info

    def reset(self):
        # """CHANGE RESET HERE""" ######################################################################################
        self.sumo_env.reset()
        ################################################################################################################

    def step(self, action):
        # """CHANGE STEP HERE""" #######################################################################################
        self.sumo_env.step(action)
        ################################################################################################################

    def reset_render(self):
        # """CHANGE RESET RENDER HERE""" ###############################################################################
        pass
        ################################################################################################################

    def step_render(self):
        # """CHANGE STEP RENDER HERE""" ################################################################################
        pass
        ################################################################################################################
