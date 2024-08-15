import socket
import struct
import select
import numpy as np
from .proto import Message, MessageSerializer, MessageType, StepType


class Messenger:
    def __init__(self, pid=0, env_id=0, host=None, port=None):
        self.pid = pid
        self.env_id = env_id
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port: int = port if port else 10086 + pid
        self.host: str = host if host else '127.0.0.1'
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.client_socket: socket.socket = None

    def listen(self):
        # print(f"Server is listening on {self.host}:{self.port}")
        self.client_socket, addr = self.server_socket.accept()
        # print(f"Connection from {addr}")

    def send(self, msg: Message):
        data = struct.pack('c', b'\x07')
        msg_bytes = MessageSerializer.serialize(msg)
        data += np.int32(len(msg_bytes)).tobytes()
        data += msg_bytes
        data += struct.pack('c', b'\x03')
        self.client_socket.send(data)

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

    def check(self):
        """
        Check if there is data available to read from the socket.
        :return:
        """
        readable, _, _ = select.select([self.client_socket], [], [], 0)
        return bool(readable)

    def receive(self, check_obs=False):
        # while not self.check():
        #     pass
        flag = self.client_socket.recv(1)
        data_length_bytes = self.client_socket.recv(4)
        data_length = struct.unpack('I', data_length_bytes)[0]
        msg_bytes = self.client_socket.recv(data_length)
        over_flag = self.client_socket.recv(1)

        assert flag[0] == 0x06 and over_flag[0] == 0x01, "Incorrect data format received from C#."
        msg = MessageSerializer.deserialize(msg_bytes)

        if check_obs:
            if not (msg.message_type == MessageType.Observation.value
                    and msg.step_type == StepType.Step.value):
                raise RuntimeError("Received message is not an observation!")

        return msg

    def is_ready(self):
        # while not self.check():
        #     pass
        msg = self.receive()
        if (msg.message_type == MessageType.Control.value
                and msg.step_type == StepType.Ready.value):
            return True
        else:
            return False

    def close(self):
        self.client_socket.close()
        self.server_socket.close()

    # def __del__(self):
    #     # print("Destroying Messenger object.")
    #     self.close()