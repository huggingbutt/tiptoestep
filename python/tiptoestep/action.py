import numpy as np
import struct


class ContinuousAction:
    def __init__(self, num):
        self._data: np.ndarray = np.zeros(num, dtype=np.float32)

    def __getitem__(self, index):
        # Include validation if necessary
        if index < 0 or index >= len(self._data):
            raise IndexError("Index out of range")
        return self._data[index]

    def __setitem__(self, index, value):
        # Include validation if necessary
        if index < 0 or index >= len(self._data):
            raise IndexError("Index out of range")
        self._data[index] = value

    @property
    def value(self):
        return self._data

    @value.setter
    def value(self, val: np.ndarray):
        # print(f"Step Action: {val}")
        if (type(val) == list
                and len(val) == self._data.shape[0]):
            self._data = np.array(val, dtype=np.float32)
        elif (type(val) == np.ndarray
              and val.shape == self._data.shape
              and val.dtype == np.float32 ):
            self._data = val
        else:
            raise RuntimeError("Unknown action type.")

    def __len__(self):
        return self._data.shape[0]


class CategoricalAction:
    def __init__(self, *values):
        self._values = set(values)  # Using a set to mimic HashSet<T>
        self._value = None  # Placeholder, will be set when Value property is used

    def set_all_actions(self, *actions):
        self._values = set(actions)  # Replaces the existing set with a new one

    def get_all_actions(self):
        return list(self._values)  # Converts the set to a list to mimic T[]

    def add_action(self, action):
        self._values.add(action)  # Adds a new action to the set

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        # Check if the value is in the set of actions
        if val not in self._values:
            # Using f-string for string formatting
            raise ValueError(f"Value must be in [{', '.join(map(str, self._values))}]")
        self._value = val

    def __len__(self):
        return len(self._values)

    def get_value_type(self):
        # This method will return the type of the first element in the set,
        # or 'NoneType' if the set is empty. It's a bit more dynamic than in C#,
        # because Python variables can change type.
        if self._values:
            return type(next(iter(self._values))).__name__
        return type(None).__name__

    def __str__(self):
        return f"Value: {self.value}  [{', '.join(map(str, self._values))}]"


class ActionSerializer:
    @staticmethod
    def serialize(action):
        if isinstance(action, ContinuousAction):
            data = struct.pack('B', 0)  # Type indicator for ContinuousAction
            data += struct.pack('I', len(action.value))
            for value in action.value:
                data += struct.pack('f', value)
            return data
        elif isinstance(action, CategoricalAction):
            data = struct.pack('B', 1)  # Type indicator for CategoricalAction
            actions = action.get_all_actions()
            data += struct.pack('I', len(actions))
            for actionValue in actions:
                data += struct.pack('I', actionValue)
            # Assuming the value is always an int; adjust as necessary
            data += struct.pack('I', action.value if action.value is not None else 0)
            return data
        else:
            raise ValueError("Unsupported action type")

    @staticmethod
    def deserialize(data):
        type_indicator = struct.unpack('B', data[0:1])[0]
        offset = 1
        if type_indicator == 0:  # ContinuousAction
            length, = struct.unpack('I', data[offset:offset+4])
            offset += 4
            action = ContinuousAction(length)
            for i in range(length):
                value, = struct.unpack('f', data[offset:offset+4])
                action[i] = np.float32(value)
                offset += 4
            return action
        elif type_indicator == 1:  # CategoricalAction
            count, = struct.unpack('I', data[offset:offset+4])
            offset += 4
            values = []
            for _ in range(count):
                value, = struct.unpack('I', data[offset:offset+4])
                values.append(value)
                offset += 4
            action = CategoricalAction(*values)
            value, = struct.unpack('I', data[offset:offset+4])
            if value in values:  # Ensure value is one of the actions
                action.value = value
            return action
        else:
            raise ValueError("Unknown action type")