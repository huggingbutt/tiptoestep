import time
from hbagent.env import Env
from hbagent.agent import Agent
from stable_baselines3.common.monitor import Monitor

if __name__ == '__main__':
    agent = Agent(0)
    env = Monitor(Env(pid=1, env_id=1, agent=agent))
    obs = env.reset()
    print(obs)
    terminated = False
    start_time = time.time()
    while not terminated:
        observation, reward, terminated, truncated, info = env.step([1, 0, 0])
        # print(observation[1])
    print(f"Elapsed {time.time() - start_time}")
    print(env.total_steps)
    env.close()