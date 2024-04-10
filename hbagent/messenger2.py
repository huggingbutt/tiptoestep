import os
import mmap
import numpy as np
import json
from typing import Dict, Tuple
from hbagent.proto import Message, message_serializer, MessageType, StepType


class Messenger:
    def __init__(self, filename, size=1024 * 16):
        if os.path.exists(filename):
            os.remove(filename)
        self.filename = filename
        self.size = size
        # Create and/or open the memory-mapped file
        with open(self.filename, "wb") as f:
            f.seek(self.size - 1)
            f.write(b'\x00')
        self.file = open(self.filename, "r+b")
        self.mm = mmap.mmap(self.file.fileno(), self.size)
        self.mm[:1] = b'\x04'

    def send(self, message: Message):
        self.mm[:1] = b'\x07'
        message_str = json.dumps(message, default=message_serializer)
        data = message_str.encode('utf-8')
        self.mm[1:5] = np.int32(len(data)).tobytes()
        self.mm[5:5+len(data)] = data
        self.mm[:1] = b'\x03'  # Set flag to indicate a new message from python is available

    def send_action(self, agent_id, step_id, action, cmds):
        msg = Message()
        msg.agent_id = agent_id
        msg.message_type = MessageType.Action.value
        msg.step_type = StepType.Step.value
        msg.step_id = step_id
        msg.action = action
        msg.cmds = cmds
        self.send(msg)

    def send_control(self, agent_id, signal, cmds=None):
        if signal not in ['reset', 'end', 'ready']:
            raise RuntimeError(f"Unable to recognize {signal} control signal.")

        msg = Message()
        msg.agent_id = agent_id
        msg.message_type = MessageType.Control.value

        if signal == 'reset':
            msg.step_type = StepType.Reset.value
        elif signal == 'end':
            msg.step_type = StepType.End.value
        elif signal == 'ready':
            msg.step_type = StepType.Ready.value

        if cmds:
            msg.cmds = cmds

        self.send(msg)

    def check(self):
        return self.mm[:1] == b'\x01'

    def check_consume(self):
        return self.mm[:1] == b'\x02'

    def receive(self, check_obs=False):
        bytes_num_b = self.mm[1:5]
        bytes_num = np.frombuffer(bytes_num_b, dtype=np.int32)[0]
        message_b = self.mm[5:5+bytes_num]
        message = json.loads(message_b.decode())
        self.mm[:1] = b'\x04'  # Observation message from C# has been received.

        if check_obs:
            if not (message['message_type'] == MessageType.Observation.value
                    and message['step_type'] == StepType.Step.value):
                raise RuntimeError("Received message is not an observation!")

        return message

    def is_ready(self):
        while not self.check():
            pass

        msg = self.receive()
        if (msg['message_type'] == MessageType.Control.value
                and msg['step_type'] == StepType.Ready.value):
            return True
        else:
            return False

    def check_accident(self, raise_=False) -> Tuple[bool, str]:
        if self.mm[:1] == b'\x05':
            message = self.receive()
            if (message['message_type'] == MessageType.Control.value
                    and message['step_type'] == StepType.End.value):
                if raise_:
                    raise RuntimeError("Env is stopped.")
                return True, "Env is stopped."
        return False, ""

    def close(self):
        self.mm.close()
        self.file.close()

        if os.path.exists(self.filename):
            os.remove(self.filename)