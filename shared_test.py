import atexit
import time
import os
from hbagent.env import Env
from hbagent.agent import Agent
from hbagent.action import ContinuousAction
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
import signal
import sys

env_filename = '/Users/admin/libs/Juggle/JuggleSharedServer/huggingbutt_agent'

def make_env(pid):
    def _init():
        agent = Agent(0)
        action = ContinuousAction(3)
        env = Monitor(Env(pid=pid, env_id=1, agent=agent, action=action, exe_file=env_filename, time_scale=20))
        return env
    return _init

if __name__ == '__main__':
    # env = Monitor(Env(pid=0, env_id=1, agent=agent, action=action, exe_file=env_filename, time_scale=20))
    envs = [make_env(pid) for pid in range(4)]
    env = SubprocVecEnv(envs)
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=2048,
        tensorboard_log="./logs/", policy_kwargs={'net_arch': [512, 128]})

    model.learn(total_timesteps=20_000_000)
    model.save(f"juggle.zip")

    env.close()

    def clear_function():
        # subproc_envs.close()
        env.close()


    atexit.register(clear_function)