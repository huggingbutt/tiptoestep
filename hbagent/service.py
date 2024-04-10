import socket
import numpy as np


def recv(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def parse_header(header):
    env_idx = np.frombuffer(header[0:2], dtype=np.uint16)
    agent_idx = np.frombuffer(header[2:4], dtype=np.uint16)
    message_type = np.frombuffer(header[4:5], dtype=np.int8)
    step_type = np.frombuffer(header[5:6], dtype=np.int8)
    data_type = np.frombuffer(header[6:7], dtype=np.int8)
    data_size = np.frombuffer(header[7:11], dtype=np.int32)
    return env_idx[0], agent_idx[0], message_type[0], step_type[0], data_type[0], data_size[0]


def recv_msg(sock):
    msg_header = recv(sock, 15)
    if not msg_header:
        return None
    env_idx, agent_idx, message_type, step_type, data_type, data_size = parse_header(msg_header)
    data_length = data_size * np.dtype(np.float64).itemsize
    return recv(sock, data_length)
