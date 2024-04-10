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

agent = Agent(0)
# exe_file = "/Users/admin/libs/Juggle/juggle.app/Contents/MacOS/roller_ball"
juggle_exe_file = "/Users/admin/libs/Juggle/juggle.app/Contents/MacOS/roller_ball"

start_time = time.time()


def make_env(pid):
    def _init():
        env = Monitor(Env(pid=pid, env_id=1, agent=agent, exe_file=juggle_exe_file, time_scale=10))
        return env
    return _init


class MyCallback(BaseCallback):
    def _on_training_start(self) -> None:
        print(f"{os.getpid()} Training is start, {time.time()}")

    def _on_training_end(self) -> None:
        # print(f"Training is end, {time.time()}")
        pass

    def _on_step(self) -> bool:
        # print(f"{os.getpid()}  env.step(), {time.time()}")
        if self.model.rollout_buffer.size() == 512:
            print(f"current buffer size is {self.model.rollout_buffer.size()}, time elapsed {time.time() - start_time}")
        return True

    def _on_rollout_start(self) -> None:
        print(f"{os.getpid()}  collecting a new sample. {time.time()}")
        print(f"current buffer size is {self.model.rollout_buffer.size()}")

    def _on_rollout_end(self) -> None:
        print(f"rollout buffer size: {self.model.rollout_buffer.size()}")
        print(f"{os.getpid()}  update the policy, {time.time()}")


class RewardLogger(BaseCallback):
    def __init__(self, check_freq):
        super(RewardLogger, self).__init__()
        self.check_freq = check_freq
        self.best_mean_reward = -np.inf

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # Retrieve training environment
            env = self.training_env

            # Compute mean reward
            mean_reward = np.mean(env.get_attr('episode_reward'))
            print(f"Mean reward: {mean_reward} - Last {self.check_freq} steps")

            # Update the best mean reward
            if mean_reward > self.best_mean_reward:
                self.best_mean_reward = mean_reward
        return True


# from stable_baselines3 import PPO
#
# model = PPO("MlpPolicy", "CartPole-v1", verbose=1, n_steps=256, batch_size=32, learning_rate=3e-4, gamma=0.99, gae_lambda=0.99, n_epochs=3, policy_kwargs=dict(net_arch=[256]*4))
# model.learn(total_timesteps=5000000)

if __name__ == '__main__':
    # envs = [make_env(pid) for pid in range(3)]
    # subproc_envs = SubprocVecEnv(envs)
    env = Monitor(Env(pid=0, env_id=1, agent=agent, exe_file=juggle_exe_file, time_scale=10))
    model = PPO("MlpPolicy", env, verbose=1,
                tensorboard_log="./logs/ppo_juggle_fixed_v9/", policy_kwargs={'net_arch': [256, 256, 256, 64]})

    model.learn(total_timesteps=3_000_000)
    model.save(f"juggle_ts_3m_fixed_new_v10.zip")

    # previous_steps = 5
    # previous_model = f"juggle_ts_{previous_steps}m_v7_fixed_v5"
    #
    # for i in range(10):
    #     print(f"learning {previous_steps+i}m-{previous_steps+i+1}m steps...")
    #     model = PPO.load(f"{previous_model}.zip", subproc_envs, verbose=0,
    #                      tensorboard_log="./ppo_juggle_fixed_v4/", batch_size=1024)
    #     model.learn(total_timesteps=1_000_000)
    #     model.save(f"juggle_ts_{previous_steps+i+1}m_v7_fixed_v5")
    #     previous_model = f"juggle_ts_{previous_steps+i+1}m_v7_fixed_v5"

    def clear_function():
        # subproc_envs.close()
        env.close()


    atexit.register(clear_function)

# if __name__ == '__main__':
#     env = Monitor(Env(pid=0, env_id=1, agent=agent, exe_file=juggle_exe_file, time_scale=10, max_steps=1000))
#     obs = env.reset()
#     terminated = False
#     truncated = False
#     start_time = time.time()
#     while not terminated and not truncated:
#         observation, reward, terminated, truncated, info = env.step([1, 0, 0])
#         print(observation[1])
#     print(f"Elapsed {time.time() - start_time}")
#     print(env.total_steps)
#     env.close()
