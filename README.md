# Tiptoe Step
This project aims to streamline the creation of reinforcement learning environments. I intend to add support for more software(Unreal Engine, Godot, FreeCAD) to enhance its functionality.
The current version implements IPC(inter-process communication) using shared memory (mmap package in Python, 'System.IO.MemoryMappedFiles' in C#). 
It has not passed testing on Windows system, and future versions may use a different method.


## Installation

### Python

from source code
```shell
git clone -b v0.0.1 https://github.com/huggingbutt/tiptoestep.git
cd tiptoestep/python
python -m pip install .
```

### Unity
Installing tiptoestep pacakge from local disk.

'Windows' -> 'Package Manager' -> '+' -> 'Add package from disk...'

navigate to 'unity/com.huggingbutt.tiptoestep' folder and select pacakge.json for installation.

## Quickstart
Youtube[in English]:

Bilibili[in Chinese]:
