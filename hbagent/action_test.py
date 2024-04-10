from hbagent.action import ActionSerializer, ContinuousAction, CategoricalAction
import mmap
import numpy as np
from hbagent.proto import Message, MessageSerializer, MessageType, StepType
from hbagent.utils import StrDictionarySerializer
import struct

if __name__ == '__main__':
    filename = "/Users/admin/.cache/hbagent/0_1.mmf"
    file = open(filename, "r+b")
    mm = mmap.mmap(file.fileno(), 1024 * 16)
    data = mm[:266]

    msg = MessageSerializer.deserialize(data)
    print(msg.observation)
    mm.close()
    file.close()


