import atexit
from hbagent.env import Env
from hbagent.agent import Agent
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

agent = Agent(0)
# juggle_exe_file = "/Users/admin/libs/Juggle/juggle.app/Contents/MacOS/roller_ball"
juggle_exe_file = "/Users/admin/libs/Juggle/juggle_server/roller_ball"

if __name__ == '__main__':
    env = Monitor(Env(pid=0, env_id=1, agent=agent, exe_file=None, time_scale=20))
    model = PPO("MlpPolicy", env, verbose=0, n_steps=2048,
                tensorboard_log="./logs/ppo_juggle_fixed_v13/", policy_kwargs={'net_arch': [256, 256, 64]})
    model.learn(total_timesteps=10_000_000)
    model.save(f"juggle_ts_3m_fixed_new_v10.zip")

    def clear_function():
        # subproc_envs.close()
        env.close()


    atexit.register(clear_function)