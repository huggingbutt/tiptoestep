import redis
import json
from typing import Dict, Tuple
from hbagent.proto import Message, message_serializer, MessageType, StepType


class Messenger:
    def __init__(self, host='localhost', port=6379):
        self.r = redis.Redis(host=host, port=port)

    def send(self, act_key, message: Message):
        message_str = json.dumps(message, default=message_serializer)
        # print(message_str)
        self.r.rpush(act_key, message_str.encode("utf-8"))

    def send_action(self, act_key, agent_id, step_id, action, cmds):
        # push action message to Redis
        msg = Message()
        msg.agent_id = agent_id
        msg.message_type = MessageType.Action.value
        msg.step_type = StepType.Step.value
        msg.step_id = step_id
        msg.action = action
        msg.cmds = cmds
        self.send(act_key, msg)

    def send_reset(self, act_key, agent_id, cmds):
        reset_msg = Message()
        reset_msg.agent_id = agent_id
        reset_msg.message_type = MessageType.Control.value
        reset_msg.step_type = StepType.Reset.value
        reset_msg.cmds = cmds
        # Not setting msg.step_id due to -1 being unsuitable for 'UInt32', and 'Reset()' doesn't require this property.
        # print("Sending:", message_str)
        self.send(act_key, reset_msg)

    def receive(self, obs_key, accident_key, check_obs=False) -> Dict:
        self.check_healthy(obs_key, accident_key)
        msg = self.lpop(obs_key)
        # print(msg)
        if check_obs:
            if msg['message_type'] == MessageType.Observation.value and msg['step_type'] == StepType.Step.value:
                return msg
            else:
                raise RuntimeError("Received message is not an observation!")
        else:
            return msg

    def is_ready(self, obs_key, accident_key):
        msg = self.receive(obs_key, accident_key)
        if (msg['message_type'] == MessageType.Control.value
                and msg['step_type'] == StepType.Ready.value):
            return True
        else:
            return False

    def lpop(self, key):
        message_bytes = self.r.lpop(key)
        message = json.loads(message_bytes.decode('utf-8'))
        return message

    def check_accident(self, accident_key, raise_=False) -> Tuple[bool, str]:
        if self.r.llen(accident_key) > 0:
            message = self.lpop(accident_key)
            if (message['message_type'] == MessageType.Control.value
                    and message['step_type'] == StepType.End.value):
                if raise_:
                    raise RuntimeError("Env is stopped.")
                return True, "Env is stopped."
        return False, ""

    def check_healthy(self, obs_key, accident_key):
        while self.r.llen(obs_key) <= 0:
            accident, message = self.check_accident(accident_key)
            if accident:
                raise RuntimeError(message)

    def clear(self, key):
        self.r.delete(key)

