import numpy as np
from typing import Dict
from stable_baselines3 import PPO

from hbagent.env import Env
from hbagent.action import ContinuousAction
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from gymnasium import spaces


def transform_fun(obs):
    return np.array([
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
    ], dtype=np.float32)


def reward_fun(obs):
    if obs.distance <= 1.42:
        return 1.0
    else:
        return 0.0


def control_fun(obs) -> Dict[str, str]:
    response = {}
    if obs.distance <= 1.42:
        response['terminated'] = 'true'

    if obs.player_position_y <= 0:
        response['terminated'] = 'true'
        response['re-entry'] = 'true'
    return response


exe_file = "your_env_path/roller_ball/roller_ball.app/Contents/MacOS/rollerball"


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


def make_a_env():
    action = ContinuousAction(2)
    action_space = spaces.Box(low=-1.0, high=1.0, shape=(len(action),), dtype=np.float32)
    observation_space = spaces.Box(low=-np.infty, high=np.infty, shape=(12,), dtype=np.float32)
    myenv = Env(
                pid=1,
                env_id=2,
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


if __name__ == '__main__':
    envs = [make_env(pid) for pid in range(4)]
    env = SubprocVecEnv(envs)
    # env = make_a_env()
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=256,
        tensorboard_log="./logs")

    model.learn(total_timesteps=2_000_000)
    model.save(f"roller_ball.zip")

    env.close()
