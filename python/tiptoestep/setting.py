from enum import Enum


class MsgType(Enum):
    pass


class DataType(Enum):
    FLOAT64 = 1
    INT32 = 2
    STRING = 3


class StepType(Enum):
    EMPTY = 1
    ACTION = 2
    STATE = 3

