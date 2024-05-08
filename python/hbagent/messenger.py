import os
import mmap
from typing import Tuple
import numpy as np
from hbagent.proto import Message, MessageSerializer, MessageType, StepType


class Messenger:
    def __init__(self, filename, size=1024 * 16, pid=0, env_id=0):
        if os.path.exists(filename):
            os.remove(filename)
        self.filename = filename
        self.size = size
        self.pid = pid
        self.env_id = env_id
        # Create and/or open the memory-mapped file
        with open(self.filename, "wb") as f:
            f.seek(self.size - 1)
            f.write(b'\x00')
        self.file = open(self.filename, "r+b")
        self.mm = mmap.mmap(self.file.fileno(), self.size)

    def send(self, msg: Message):
        self.mm[:1] = b'\x07'  # Python side is writing data.
        data = MessageSerializer.serialize(msg)
        self.mm[1: 5] = np.int32(len(data)).tobytes()
        self.mm[5: 5+len(data)] = data
        self.mm[: 1] = b'\x03'  # A new message (action message) form Python is available

    def send_action(self, agent_id, step_id, action, cmds=None):
        msg = Message()
        msg.pid = self.pid
        msg.env_id = self.env_id
        msg.agent_id = agent_id
        msg.step_id = step_id
        msg.obs_frame_id = 0
        msg.act_frame_id = 0
        msg.silent = False
        msg.message_type = MessageType.Action.value
        msg.step_type = StepType.Step.value
        msg.action = action
        msg.cmds = cmds
        self.send(msg)

    def send_control(self, agent_id, step_id, signal, cmds=None):
        if signal not in ['reset', 'end', 'ready']:
            raise RuntimeError(f"Unable to recognize {signal} control signal.")

        msg = Message()
        msg.pid = self.pid
        msg.env_id = self.env_id
        msg.agent_id = agent_id
        msg.step_id = step_id
        msg.obs_frame_id = 0
        msg.act_frame_id = 0
        msg.silent = False
        msg.message_type = MessageType.Control.value

        if signal == 'reset':
            msg.step_type = StepType.Reset.value
        elif signal == 'end':
            msg.step_type = StepType.End.value
        elif signal == 'ready':
            msg.step_type = StepType.Ready.value

        msg.cmds = cmds
        self.send(msg)

    def receive(self, check_obs=False):
        bytes_num_b = self.mm[1:5]
        bytes_num = np.frombuffer(bytes_num_b, dtype=np.int32)[0]
        msg_b = self.mm[5:5 + bytes_num]
        msg = MessageSerializer.deserialize(msg_b)
        self.mm[:1] = b'\x04'  # Observation message from C# has been received.

        if check_obs:
            if not (msg.message_type == MessageType.Observation.value
                    and msg.step_type == StepType.Step.value):
                raise RuntimeError("Received message is not an observation!")

        return msg

    def check(self):
        # Check for the arrival of the observation message.
        # 'agent_id' needs to be added to mark the observations seen by an agent in subsequent version.
        return self.mm[:1] == b'\x01'

    def check_accident(self, raise_=False) -> Tuple[bool, str]:
        if self.mm[:1] == b'\x05':
            message = self.receive()
            if (message['message_type'] == MessageType.Control.value
                    and message['step_type'] == StepType.End.value):
                if raise_:
                    raise RuntimeError("Env is stopped.")
                return True, "Env is stopped."
        return False, ""

    def is_ready(self):
        while not self.check():
            pass

        msg = self.receive()
        if (msg.message_type == MessageType.Control.value
                and msg.step_type == StepType.Ready.value):
            return True
        else:
            return False

    def close(self):
        self.mm.close()
        self.file.close()

        if os.path.exists(self.filename):
            os.remove(self.filename)
