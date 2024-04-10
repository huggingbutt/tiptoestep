import os
import io
import struct
from pathlib import Path
import numpy as np
from typing import Optional, Dict
from collections import namedtuple

cache_path = "~/.cache/hbagent"
real_cache_path = os.path.expanduser(cache_path)


def create_default_mmf(pid, env_id):
    mmf = os.path.join(real_cache_path, f"{pid}_{env_id}.mmf")
    parent_path = os.path.dirname(real_cache_path)
    Path(parent_path).mkdir(parents=True, exist_ok=True)
    return mmf


class StrDictionarySerializer:
    @staticmethod
    def serialize(dictionary):
        with io.BytesIO() as byte_stream:
            for key, value in dictionary.items():
                key_bytes = key.encode('utf-8')
                value_bytes = value.encode('utf-8')

                # Write the length of the key and value
                byte_stream.write(struct.pack('I', len(key_bytes)))
                byte_stream.write(struct.pack('I', len(value_bytes)))

                # Write the actual key and value bytes
                byte_stream.write(key_bytes)
                byte_stream.write(value_bytes)

            return byte_stream.getvalue()

    @staticmethod
    def deserialize(byte_array):
        dictionary = {}
        with io.BytesIO(byte_array) as byte_stream:
            while True:
                lengths = byte_stream.read(8)
                if not lengths:
                    break

                key_length, value_length = struct.unpack('II', lengths)

                # Read the key and value bytes
                key_bytes = byte_stream.read(key_length)
                value_bytes = byte_stream.read(value_length)

                # Convert bytes back to strings and add to the dictionary
                key = key_bytes.decode('utf-8')
                value = value_bytes.decode('utf-8')
                dictionary[key] = value

        return dictionary




class ObservationSerializer:
    @staticmethod
    def deseriazlie(byte_array): # return
        pass



        # Observation = namedtuple('Observation', obs_dict.keys())
        # obs = Observation(**obs_dict)