import io
import json
import struct
from enum import Enum
import numpy as np
from typing import Dict, Union

from .action import CategoricalAction, ContinuousAction, ActionSerializer
from .utils import StrDictionarySerializer


class MessageType(Enum):
    Observation = 0
    Action = 1
    Control = 2


class StepType(Enum):
    Ready = 0
    Wait = 1
    Step = 2
    End = 3
    Reset = 4
    Start = 5


class Message:
    def __init__(self):
        self.pid = 0
        self.env_id = 0
        self.agent_id = 0
        self.message_type: MessageType = MessageType.Control  # Should be an instance of MessageType
        self.step_type: StepType = StepType.Step  # Should be an instance of StepType
        self.step_id = 0
        self.obs_frame_id = 0
        self.act_frame_id = 0
        self.silent: bool = False
        self.observation: Dict[str, Union[np.float32, bool]] = {}  # Should be a dict object
        self.action = None  # This is meant to be an interface in C#, you might use a base class or protocol in Python
        self.cmds = {}  # Should be an instance of Dict<string, string>


def observation_to_dict(byte_array) -> Dict[str, Union[np.float32, bool]]:
    """
    Deserializes a byte array into a dictionary representing an Observation object.
    The byte array must follow the structure defined in the C# SerializeToBytes method.
    """
    deserialized_data = {}

    with io.BytesIO(byte_array) as stream:
        while stream.tell() < len(byte_array):
            # Read the length of the property name
            name_length = struct.unpack('i', stream.read(4))[0]

            # Read the property name
            pname = stream.read(name_length).decode('utf-8')

            # Read the type identifier
            type_identifier = struct.unpack('i', stream.read(4))[0]

            # Depending on the type identifier, read the value
            if type_identifier == 0:  # float
                value = np.float32(struct.unpack('f', stream.read(4))[0])
            elif type_identifier == 1:  # bool
                value = struct.unpack('?', stream.read(1))[0]
            else:
                raise ValueError("Unknown type identifier encountered.")

            # Add the property and its value to the dictionary
            deserialized_data[pname] = value

    return deserialized_data


class MessageSerializer:
    @staticmethod
    def serialize(msg: Message) -> bytes:
        data  = struct.pack('I', np.uint32(msg.pid))
        data += struct.pack('I', np.uint32(msg.env_id))
        data += struct.pack('I', np.uint32(msg.agent_id))
        data += struct.pack('I', np.uint32(msg.step_id))
        data += struct.pack('I', np.uint32(msg.obs_frame_id))
        data += struct.pack('I', np.uint32(msg.act_frame_id))
        data += struct.pack('?', np.uint32(msg.silent))
        data += struct.pack('i', np.uint32(msg.message_type))
        data += struct.pack('i', np.uint32(msg.step_type))

        if msg.action is None:
            data += struct.pack('i', 0)
        else:
            action_bytes = ActionSerializer.serialize(msg.action)
            data += struct.pack('i', len(action_bytes))
            data += action_bytes

        # print(len(data))

        if msg.cmds is None:
            data += struct.pack('i', 0)
        else:
            cmds_bytes = StrDictionarySerializer.serialize(msg.cmds)
            # print(len(cmds_bytes))
            data += struct.pack('i', len(cmds_bytes))
            data += cmds_bytes

        if len(msg.observation) <= 0:
            data += struct.pack('i', 0)
        else:
            data += struct.pack('i', len(msg.observation))
            data += msg.observation

        # print(len(data))

        return data

    @staticmethod
    def deserialize(data: bytes):
        msg = Message()
        msg.pid = np.uint32(struct.unpack('I', data[0:4])[0])
        msg.env_id = np.uint32(struct.unpack('I', data[4:8])[0])
        msg.agent_id = np.uint32(struct.unpack('I', data[8:12])[0])
        msg.step_id = np.uint32(struct.unpack('I', data[12:16])[0])
        msg.obs_frame_id = np.uint32(struct.unpack('I', data[16:20])[0])
        msg.act_frame_id = np.uint32(struct.unpack('I', data[20:24])[0])
        msg.silent = np.uint32(struct.unpack('?', data[24:25])[0])
        msg.message_type = np.int32(struct.unpack('i', data[25:29])[0])
        msg.step_type = np.int32(struct.unpack('i', data[29:33])[0])

        offset = 33
        action_len = np.int32(struct.unpack('i', data[offset:offset + 4])[0])
        offset += 4
        if action_len > 0:
            msg.action = ActionSerializer.deserialize(data[offset:offset + action_len])
            offset += action_len

        cmds_len = np.int32(struct.unpack('i', data[offset:offset + 4])[0])
        offset += 4
        if cmds_len > 0:
            msg.cmds = StrDictionarySerializer.deserialize(data[offset:offset + cmds_len])
            offset += cmds_len

        obs_len = np.int32(struct.unpack('i', data[offset:offset + 4])[0])
        offset += 4
        if obs_len > 0:
            msg.observation = observation_to_dict(data[offset:offset + obs_len])

        return msg

    @staticmethod
    def to_str(msg: Message):
        str_ = ""
        str_ += f"pid : {msg.pid}\n"
        str_ += f"env_id : {msg.env_id}\n"
        str_ += f"agent_id : {msg.agent_id}\n"
        str_ += f"step_id : {msg.step_id}\n"
        str_ += f"act_frame_id : {msg.act_frame_id}\n"
        str_ += f"obs_frame_id : {msg.obs_frame_id}\n"
        str_ += f"silent : {msg.silent}\n"
        str_ += f"message_type : {msg.message_type}\n"
        str_ += f"step_type : {msg.step_type}\n"
        str_ += f"action : {msg.action}\n"
        str_ += f"cmds : {msg.cmds}\n"
        str_ += f"observation : {json.dumps(observation_to_dict(msg.observation))}"


def message_serializer(obj):
    if isinstance(obj, CategoricalAction):
        if not any([isinstance(obj.value, str), isinstance(obj.value, int)]):
            raise RuntimeError("Unknown value type")
        return {
            "action_type": "CategoricalAction`1",
            "all_actions": obj.get_all_actions(),
            "value_type": "String" if isinstance(obj.value, str) else "Int32",
            "value": obj.value
        }

    if isinstance(obj, ContinuousAction):
        return {
            "action_type": "ContinuousAction",
            "value": obj.value
        }

    if isinstance(obj, Message):
        return {
            "pid": obj.pid,
            "env_id": obj.env_id,
            "agent_id": obj.agent_id,
            "message_type": obj.message_type,
            "step_type": obj.step_type,
            "step_id": obj.step_id,
            "observation": obj.observation,
            "action": obj.action,
            "cmds": obj.cmds
        }


def message_deserializer(obj):
    pass

