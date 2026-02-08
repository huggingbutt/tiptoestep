import socket
import struct
import select
import numpy as np
from .proto import Message, MessageSerializer, MessageType, StepType
from typing import Optional


class Messenger:
    def __init__(self, pid=0, env_id=0, host=None, port=None, timeout: Optional[float] = None):
        self.pid = pid
        self.env_id = env_id
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Reuse address to reduce TIME_WAIT issues during rapid restarts
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port: int = port if port else 10086 + pid
        self.host: str = host if host else '127.0.0.1'
        self.timeout = timeout
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.client_socket: socket.socket = None

    def listen(self):
        # print(f"Server is listening on {self.host}:{self.port}")
        self.client_socket, addr = self.server_socket.accept()
        # Disable Nagle to reduce latency for small control packets
        try:
            self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        if self.timeout is not None:
            try:
                self.client_socket.settimeout(self.timeout)
            except Exception:
                pass
        # print(f"Connection from {addr}")

    def send(self, msg: Message):
        data = struct.pack('c', b'\x07')
        msg_bytes = MessageSerializer.serialize(msg)
        # Use little-endian explicit packing for length
        data += struct.pack('<I', int(len(msg_bytes)))
        data += msg_bytes
        data += struct.pack('c', b'\x03')
        # Ensure full write over TCP
        self.client_socket.sendall(data)

    def _read_exact(self, n: int) -> bytes:
        """Read exactly n bytes from the client socket or raise if connection closes early."""
        buf = bytearray()
        while len(buf) < n:
            chunk = self.client_socket.recv(n - len(buf))
            if not chunk:
                raise RuntimeError("Socket closed while reading data")
            buf += chunk
        return bytes(buf)

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
        # Read framed packet: [0x06][len(4 LE)][payload][0x01]
        flag = self._read_exact(1)
        data_length_bytes = self._read_exact(4)
        data_length = struct.unpack('<I', data_length_bytes)[0]
        msg_bytes = self._read_exact(data_length)
        over_flag = self._read_exact(1)

        assert flag[0] == 0x06 and over_flag[0] == 0x01, "Incorrect data format received from C#."
        msg = MessageSerializer.deserialize(msg_bytes)

        if check_obs:
            if not (msg.message_type == MessageType.Observation.value
                    and msg.step_type == StepType.Step.value):
                raise RuntimeError("Received message is not an observation!")

        return msg

    def is_ready(self):
        # Wait and consume a Ready control message
        msg = self.receive()
        if (msg.message_type == MessageType.Control.value
                and msg.step_type == StepType.Ready.value):
            return True
        else:
            return False

    def close(self):
        try:
            if self.client_socket is not None:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.client_socket.close()
        finally:
            if self.server_socket is not None:
                self.server_socket.close()

    # def __del__(self):
    #     # print("Destroying Messenger object.")
    #     self.close()