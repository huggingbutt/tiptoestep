import os.path
import subprocess
import numpy as np
import gymnasium as gym
from collections import namedtuple
from typing import Any, Union, Callable, Dict, Type
from action import ContinuousAction, CategoricalAction
from agent import Agent
from proto import Message
from messenger import Messenger
from utils import create_default_mmf


# todo
def check_function(function: Callable, input_t: Type, out_t: Type) -> bool:
    # Check if user-provided function meets the requirements.
    return True


class Env(gym.Env):
    def __init__(self,
                 action: Union[ContinuousAction, CategoricalAction],
                 action_space,
                 observation_space,
                 transform_fun: Callable,
                 reward_fun: Callable,
                 control_fun: Callable,
                 pid=0,
                 env_id=0,
                 agent: Agent = None,
                 time_scale=1,
                 max_steps=10000,
                 mmf=None,
                 exe_file=None):
        super(Env, self).__init__()
        self.pid = pid
        self.env_id = env_id
        self.agent = Agent(0) if agent is None else agent
        self.time_scale = time_scale
        self.action = action
        self.action_space = action_space
        self.observation_space = observation_space
        self.step_id = 0
        self.max_steps = max_steps
        self.total_reward = 0.0
        self.step_reward = 0.0
        self.terminated = False
        self.truncated = False
        self.cmds = {}
        self.env_running = True
        self.reward_fun = reward_fun
        self.control_fun = control_fun
        self.transform_fun = transform_fun

        if mmf and os.path.isfile(mmf):
            self.mmf = mmf
        else:
            self.mmf = create_default_mmf(pid, env_id)

        self.messenger = Messenger(self.mmf)

        self.exe_file = None

        if exe_file:
            self.exe_file = [exe_file, f"-pid={self.pid}", f"-env_id={self.env_id}", f"-mmf={self.mmf}"]
            if time_scale != 1:
                self.exe_file.append(f"-time_scale={time_scale}")
            self.process = subprocess.Popen(self.exe_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not self.messenger.is_ready():
            raise RuntimeError("Environment initialization failed!!")

    def processing_message(self, msg: Message, reset=False, check_sync=True):
        # pid = message['pid']
        # env_id = message['env_id']
        # agent_id = message['agent_id']
        # print(f"RECEIVED:{message}")
        info = {}
        self.cmds = {}
        step_id = msg.step_id
        if check_sync:
            # print(f"New observation step_id:{step_id}, env step_id:{self.step_id}.")
            if not reset:
                if step_id - self.step_id != 1:
                    raise RuntimeError(f"New observation step_id:{step_id}, env step_id:{self.step_id}.")
            else:
                assert step_id == 0, "Step id is not 0."

        obs_dict = msg.observation
        Observation = namedtuple('Observation', obs_dict.keys())
        obs = Observation(**obs_dict)
        # Calculate current step reward using one user's reward_fun
        self.step_reward = self.reward_fun(obs)

        response = self.control_fun(obs)
        if 'terminated' in response and response['terminated']:
            terminated = True
        else:
            terminated = False
        if 'truncated' in response and response['truncated']:
            truncated = True
        else:
            truncated = False
        # print(f"response:{response}")
        # Determine if the next action message includes external commands.
        # Commands contained in the action message with the same step_id as the observation message.
        # self.cmds will send to local env at next action message with action info.
        for k, v in response.items():
            if k not in ['truncated', 'terminated']:
                self.cmds[k] = v
                info[k] = v

        obs_processed = self.transform_fun(obs)

        return obs_processed, self.step_reward, terminated, truncated, info

    def step(self, action: np.ndarray):
        # self.messenger.check_accident(raise_=True)
        # con_action = ContinuousAction(len(action))
        self.action.value = action

        # print(self.cmds)
        self.messenger.send_action(self.agent.id, self.step_id, self.action, self.cmds)

        # while not self.messenger.check_consume():
        #     # Waiting for current action message to be consumed by C#
        #     time.sleep(0.001)

        # print(f"Step ID {self.step_id}")
        # Receive observation message after take the action
        while not self.messenger.check():
            # Pending production of a new observation message by C#
            # time.sleep(0.001)
            pass

        obs_messge = self.messenger.receive(check_obs=True)
        # check agent_id in obs_msg
        # Current version supports only one agent. agent id is 0.

        obs_processed, step_reward, terminated, truncated, info = self.processing_message(obs_messge)

        if truncated is False and self.step_id >= self.max_steps:
            truncated = True

        self.step_id = obs_messge.step_id
        # print(f"New Step ID {self.step_id}")
        self.total_reward += step_reward
        self.step_reward = 0
        return np.array(obs_processed), step_reward, terminated, truncated, info

    def reset(self,
              *,
              seed: int = 10086,
              options: dict[str, Any] = None
              ):
        self.messenger.check_accident(raise_=True)
        # print(self.cmds)
        self.messenger.send_control(self.agent.id, self.step_id, 'reset', self.cmds)
        # while not self.messenger.check_consume():
        #     pass

        while not self.messenger.check():
            pass
        obs_message = self.messenger.receive(check_obs=True)
        # check agent_id in obs_msg
        # Current version supports only one agent. agent id is 0.

        obs_processed, step_reward, terminated, truncated, info = self.processing_message(obs_message, reset=True)
        self.step_id = obs_message.step_id
        return np.array(obs_processed), info

    def close(self):
        self.messenger.send_control(self.agent.id, self.step_id, 'end')
        self.messenger.close()
        if self.exe_file is not None and self.process is not None:
            stdout, stderr = self.process.communicate()
            print(f"output:{stdout}")
            self.process.terminate()
            self.process.wait()




# roller ball's reward function

# def reward_fun(obs):
#     if obs.distance <= 1.42:
#         return 1.0
#     else:
#         return 0.0


# def reward_fun(obs):
#     # reward = 0.0
#     # if obs.diff > 0 >= obs.previous_diff and obs.collied is True:
#     #     reward += 1.0
#     #
#     # print(np.sqrt(obs.ball_position_x ** 2 + obs.ball_position_z ** 2) / 14)
#     # return reward
#     step_reward = 0.0
#     if obs.diff > 0 > obs.previous_diff and obs.collied is True:
#         step_reward += 1
#
#     # step_reward -= np.sqrt(obs.ball_position_x ** 2 + obs.ball_position_z ** 2) / 14
#     return step_reward
#
#
# def control_fun(obs):
#     response = {}
#     if (obs.ball_position_y <= 1.5
#             # or obs.player_position_y <= 0
#             or abs(obs.player_position_x) >= 10
#             or abs(obs.player_position_z) >= 10):
#         response['terminated'] = True
#     return response
#
#
# # roller ball 's control_fun
# # def feedback_fun(obs):
# #     # Game terminated if target-player distance < 1.42 or player's y < 0
# #     # The game terminated if either distance between the target and player is less than 1.42,
# #     # or if the player's y-coordinate falls below zero.
# #     response = {}
# #     if obs.distance <= 1.42:
# #         response['terminated'] = True
# #
# #     if obs.player_position_y <= 0:
# #         response['terminated'] = True
# #         response['re-entry'] = True
# #
# #     return response
#
#
# def transform_fun(obs):
#     return np.array([
#         obs.ball_position_x,
#         obs.ball_position_y,
#         obs.ball_position_z,
#         obs.ball_velocity_x,
#         obs.ball_velocity_y,
#         obs.ball_velocity_z,
#         obs.ball_rotation_x,
#         obs.ball_rotation_y,
#         obs.ball_rotation_z,
#         obs.ball_rotation_w,
#         obs.ball_angular_velocity_x,
#         obs.ball_angular_velocity_y,
#         obs.ball_angular_velocity_z,
#         obs.player_position_x,
#         obs.player_position_y,
#         obs.player_position_z,
#         obs.player_velocity_x,
#         obs.player_velocity_y,
#         obs.player_velocity_z,
#         obs.player_rotation_x,
#         obs.player_rotation_y,
#         obs.player_rotation_z,
#         obs.player_rotation_w,
#         obs.player_angular_velocity_x,
#         obs.player_angular_velocity_y,
#         obs.player_angular_velocity_z
#     ])

# roller ball's transform function
# def processed_obs_fun(obs):
#     return np.array([
#         obs.target_position_x,
#         obs.target_position_y,
#         obs.target_position_z,
#         obs.player_position_x,
#         obs.player_position_y,
#         obs.player_position_z,
#         obs.player_velocity_x,
#         obs.player_velocity_y,
#         obs.player_velocity_z
#     ])