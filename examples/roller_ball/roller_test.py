import numpy as np
from stable_baselines3 import PPO

from hbagent.env import Env
from hbagent.action import ContinuousAction
from hbagent.utils import load_custom_functions
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from gymnasium import spaces


my_function_file = "my_functions.py"
exe_file = "rollerball_path"

transform_fun, reward_fun, control_fun = load_custom_functions(my_function_file)


def make_env(pid):
    def _init():
        action = ContinuousAction(2)
        action_space = spaces.Box(low=-1.0, high=1.0, shape=(len(action),), dtype=np.float32)
        observation_space = spaces.Box(low=-np.infty, high=np.infty, shape=(12,), dtype=np.float32)
        myenv = Env(pid=pid,
                    action=action,
                    action_space=action_space,
                    observation_space=observation_space,
                    transform_fun=transform_fun,
                    reward_fun=reward_fun,
                    control_fun=control_fun,
                    time_scale=20,
                    exe_file=exe_file
                    )
        myenv = Monitor(myenv)
        return myenv

    return _init


if __name__ == '__main__':
    envs = [make_env(pid) for pid in range(4)]
    env = SubprocVecEnv(envs)
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=256,
        tensorboard_log="./logs")

    model.learn(total_timesteps=200_000)
    model.save(f"roller_ball.zip")

    env.close()
