import redis
import numpy as np
import json
import gymnasium as gym
from gymnasium import spaces
from collections import namedtuple
from stable_baselines3 import PPO
from typing import Any
from hbagent.messenger import Messenger
from hbagent.proto import Message, MessageType, StepType, message_serializer
from hbagent.action import ContinuousAction, CategoricalAction

class BaseEnv(gym.Env):
    def __init__(self, pid, env_id, agent_id):
        super(BaseEnv, self).__init__()
        self.pid = pid
        self.env_id = env_id
        self.agent_id = agent_id
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float64)
        self.observation_space = spaces.Box(low=-np.infty, high=np.infty, shape=(9,), dtype=np.float64)
        self.step_id = 0
        self.total_reward = 0.0
        self.step_reward = 0.0
        self.terminated = False
        self.truncated = False
        self.cmds = {}
        self.env_running = True

        self.messenger = Messenger(pid, env_id, agent_id)
        if not self.messenger.is_ready():
            raise RuntimeError("Environment initialization failed!!")


    def processing_message(self, message):
        pid = message['pid']
        env_id = message['env_id']
        agent_id = message['agent_id']
        step_id = message['step_id']
        # print(f"New observation step_id:{step_id}, env step_id:{self.step_id}.")
        if step_id - self.step_id != 1:
            raise RuntimeError(f"New observation step_id:{step_id}, env step_id:{self.step_id}.")

        info = {}

        obs_dict = message['observation']
        Observation = namedtuple('Observation', obs_dict.keys())
        obs = Observation(**obs_dict)

        self.step_reward = reward(obs)

        response = feedback(obs)
        if 'terminated' in response and response['terminated']:
            terminated = True
        else:
            terminated = False

        if 'truncated' in response and response['truncated']:
            # All extended messages in the response will be added to the info varialbe.
            for k, v in response.items():
                if k not in ['truncated', 'terminated']:
                    info[k] = v

            truncated = True
        else:
            truncated = False

        obs_processed = processed_obs(obs)

        return obs_processed, self.step_reward, terminated, truncated, info

    def step(self, action):

        self.check_accident()
        if not self.env_running:
            raise RuntimeError("Environment inactive. Please recreate.")

        # push action message to Redis
        msg = Message()
        msg.pid = self.pid
        msg.env_id = self.env_id
        msg.agent_id = self.agent_id
        msg.message_type = MessageType.Action.value
        msg.step_type = StepType.Step.value
        msg.step_id = self.step_id
        # action variable need to processe
        con_action = ContinuousAction(len(action))
        con_action.value = action
        msg.action = con_action
        status = {"signal": "catched"}
        msg.status = status

        message_str = json.dumps(msg, default=message_serializer)
        print("Action Message:" + message_str)
        r.rpush('hb_action', message_str.encode('utf-8'))

        # received observation message from Redis
        env_running, message = self.check_healthy()
        if not env_running:
            return None, None, None, None, {'accident': message}

        message_bytes = r.lpop('hb_observation')
        message = json.loads(message_bytes.decode('utf-8'))

        obs_processed, step_reward, terminated, truncated, info = self.processing_message(message)

        self.step_id = message['step_id']
        self.total_reward += step_reward
        self.step_reward = 0
        return np.array(obs_processed), step_reward, terminated, truncated, info

    def reset(self,
              *,
              seed: int = 10086,
              options: dict[str, Any] = None
              ):
        self.check_accident()
        # print(f"Current Step id : {self.step_id}")
        if not self.env_running:
            raise RuntimeError("Environment inactive. Please recreate.")
        msg = Message()
        msg.pid = self.pid
        msg.env_id = self.env_id
        msg.agent_id = self.agent_id
        msg.message_type = MessageType.Control.value
        msg.step_type = StepType.Reset.value
        # Not setting msg.step_id due to -1 being unsuitable for 'UInt32', and 'Reset()' doesn't require this property.
        message_str = json.dumps(msg, default=message_serializer)
        # print("Sending:", message_str)
        r.rpush('hb_action', message_str.encode('utf-8'))
        # print(f"Current hb_observation {r.llen('hb_observation')}")
        env_running, message = self.check_healthy()
        if not env_running:
            # print("ACCIDENT!!")
            return None, {'accident': message}
        message_bytes = r.lpop('hb_observation')
        message = json.loads(message_bytes.decode('utf-8'))
        # print("Received:", message)
        if message['message_type'] == MessageType.Observation.value and message['step_type'] == StepType.Step.value:
            self.step_id = message['step_id']
            obs_dict = message['observation']
            Observation = namedtuple('Observation', obs_dict.keys())
            obs = Observation(**obs_dict)
            obs_processed = processed_obs(obs)
            info = {}
        else:
            raise RuntimeError("Receive message error.")

        return np.array(obs_processed), info

    def close(self):
        self._clear()


def reward(obs):
    if obs.distance <= 1.42:
        return 1.0
    else:
        return 0.0


def feedback(obs):
    # Game terminated if target-player distance < 1.42 or player's y < 0
    # The game terminated if either distance between the target and player is less than 1.42,
    # or if the player's y-coordinate falls below zero.
    response = {}
    if obs.distance <= 1.42:
        response['terminated'] = True

    if obs.player_position_y <= 0:
        response['terminated'] = True
        response['re-entry'] = True

    return response


def processed_obs(obs):
    return [
        obs.target_position_x,
        obs.target_position_y,
        obs.target_position_z,
        obs.player_position_x,
        obs.player_position_y,
        obs.player_position_z,
        obs.player_velocity_x,
        obs.player_velocity_y,
        obs.player_velocity_z
    ]

r = redis.Redis(host='localhost', port=6379)

if __name__ == '__main__':
    env = BaseEnv(pid=1, env_id=1, agent_id=1)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=10000)
