import numpy as np
from stable_baselines3 import PPO

from tiptoestep.env import Env
from tiptoestep.action import ContinuousAction
from tiptoestep.utils import load_custom_functions
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from gymnasium import spaces

EXE_FILE = "YOUR_ENV_PATH"


def transform_fun(obs):
    return np.array([
        # Write your code here.
        obs.player_position_x,
        obs.player_position_y,
        obs.player_position_z,
        obs.player_velocity_x,
        obs.player_velocity_y,
        obs.player_velocity_z,
        obs.player_angular_velocity_x,
        obs.player_angular_velocity_y,
        obs.player_angular_velocity_z,
        obs.target_position_x,
        obs.target_position_y,
        obs.target_position_z
        # End of your code.
    ], dtype=np.float32)


def reward_fun(obs):
    # Your must return a floating-point number as the reward of this step.
    # Write your reward function here.
    if obs.distance <= 1.42:
        return 1.0
    else:
        return 0.0
    # End of your code.
    # Do not alter the following line.
    return 0.0


def control_fun(obs):
    response = {}
    # Write your code here.
    if obs.distance <= 1.42:
        response['terminated'] = 'true'
    if obs.player_position_y <= 0:
        response['terminated'] = 'true'
        response['re-entry'] = 'true'
    # End of your code.
    return response


def make_an_env(exe_file):
    action = ContinuousAction(2)
    action_space = spaces.Box(low=-1.0, high=1.0, shape=(len(action),), dtype=np.float32)
    observation_space = spaces.Box(low=-np.infty, high=np.infty, shape=(12,), dtype=np.float32)
    myenv = Env(pid=0,
                action=action,
                action_space=action_space,
                observation_space=observation_space,
                transform_fun=transform_fun,
                reward_fun=reward_fun,
                control_fun=control_fun,
                time_scale=1,
                exe_file=exe_file
                )
    myenv = Monitor(myenv)
    return myenv


def make_env(pid, exe_file):
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
    # envs = [make_env(pid, EXE_FILE) for pid in range(4)]
    # env = SubprocVecEnv(envs)
    env = make_an_env(EXE_FILE)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=256,
        tensorboard_log="./logs")

    model.learn(total_timesteps=200_000)
    model.save(f"roller_ball.zip")

    env.close()
