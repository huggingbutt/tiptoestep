import atexit
import time
import os
from hbagent.env import Env
from hbagent.agent import Agent
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
import numpy as np
import signal
import sys

agent = Agent(0)
# exe_file = "/Users/admin/libs/Juggle/juggle.app/Contents/MacOS/roller_ball"
# juggle_exe_file = "/Users/admin/libs/Juggle/juggle.app/Contents/MacOS/roller_ball"
juggle_exe_file = "/Users/admin/libs/Juggle/juggle_server/roller_ball"

start_time = time.time()

def my_cleanup_function(signum, frame):
    print("Cleaning up...")
    # Place your cleanup code here
    sys.exit(0)



def make_env(pid):
    def _init():
        env = Monitor(Env(pid=pid, env_id=1, agent=agent, exe_file=juggle_exe_file, time_scale=20))
        return env
    return _init





if __name__ == '__main__':
    NUM_ENVS = 4
    BATCH_SIZE = 64
    BUFFER_SIZE = 4096
    UPDATES = 50
    TOTAL_TAINING_STEPS_GOAL = BUFFER_SIZE * UPDATES
    BETA = 0.0005
    N_EPOCHS = 10
    STEPS_PER_UPDATE = BUFFER_SIZE / NUM_ENVS


    # env = Monitor(Env(pid=0, env_id=1, agent=agent, exe_file=juggle_exe_file, time_scale=20))
    envs = [make_env(pid) for pid in range(NUM_ENVS)]
    env = SubprocVecEnv(envs)
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        # learning_rate=lambda progress: 0.0003 * (1.0 - progress),
        # clip_range=lambda progress: 0.2 * (1.0 - progress),
        # clip_range_vf=lambda progress: 0.2 * (1.0 - progress),
        # n_steps=int(STEPS_PER_UPDATE),
        n_steps=4096,
        # batch_size=BATCH_SIZE,
        # n_epochs=N_EPOCHS,
        # ent_coef=BETA,
        tensorboard_log="./logs/ppo_juggle_fixed_v14/", policy_kwargs={'net_arch': [512, 128]})

    model.learn(total_timesteps=20_000_000)
    model.save(f"juggle_newf.zip")

    env.close()


    def clear_function():
        # subproc_envs.close()
        env.close()


    # Register the signal handlers
    signal.signal(signal.SIGINT, clear_function)
    signal.signal(signal.SIGTERM, clear_function)


    atexit.register(clear_function)