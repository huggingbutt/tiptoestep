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

## Tutorial
Youtube[in English]:

Bilibili[in Chinese]:

### Python-side Tutorial
#### 1. Three Core Functions
First, we need to define the following three core functions:
1. **transform_fun**: A function to process raw observations (custom environment observation classes written by extending the Observation class in Unity) and pass the processed observations to the policy.  
2. **reward_fun**. : A function to calculate the reward for each step based on the raw observations provided by the environment.
3. **control_fun**. : A function to determine the termination logic of the environment based on raw observation and control how an episode ends.

In the roller ball example, the environment provides the following 13-dimensional raw observations.(in C# on the Unity)
```c#
using tiptoestep;

public class MyObservation : Observation
{
    // Target information
    public float target_position_x { get; set; }
    public float target_position_y { get; set; }
    public float target_position_z { get; set; }

    // Player infromation
    public float player_position_x { get; set; }
    public float player_position_y { get; set; }
    public float player_position_z { get; set; }

    public float player_velocity_x { get; set; }
    public float player_velocity_y { get; set; }
    public float player_velocity_z { get; set; }

    public float player_angular_velocity_x { get; set; }
    public float player_angular_velocity_y { get; set; }
    public float player_angular_velocity_z { get; set; }

    public float distance { get; set; }
}
```
We want the policy to receive all the information except for the distance, so we can define the `transfrom_fun` as follows:
```python
def transform_fun(obs):
  return np.array([
    # Write your code here.
    obs.player_position_x,
    obs.player_position_y,
    obs.player_position_z,
    obs.player_velocity_x,
    obs.player_velocity_y,
    obs.player_velocity_z,
    obs.player_angular_velocity_x,
    obs.player_angular_velocity_y,
    obs.player_angular_velocity_z,
    obs.target_position_x,
    obs.target_position_y,
    obs.target_position_z
    # End of your code.
  ], dtype=np.float32)
```
During the learning process, we need to provide the policy with a reward or penalty for each action taken. For the roller ball example, the player only receives a reward when it touches the target block. Therefore, we return a reward of 1 if the distance between the player and the target block is less than a threshold; otherwise, we return 0. The threshold is set to 1.42.
```python
def reward_fun(obs):
  # Your must return a floating-point number as the reward of this step.
  # Write your reward function here.
  if obs.distance <= 1.42:
    return 1.0
  else:
    return 0.0
  # End of your code.
  # Do not alter the following line.
  return 0.0
```
There are two conditions for ending a game: when the player touches the target block or falls out of the environment's floor. If the player falls out, it needs to be recalled to the environment. In Unity, the game ends normally when the distance between the player and the target block is less than 1.42. In this case, we set the `termination` variable to `true`. This value is a string.

If the player's y-coordinate is below the ground level, we set the `re-entry` variable to `true`. The `re-entry` variable is custom-defined in the Unity environment with corresponding logic, while the `termination` variable is system-defined and requires no additional design in Unity.
```python
def control_fun(obs):
  response = {}
  # Write your code here.
  if obs.distance <= 1.42:
    response['terminated'] = 'true'
  if obs.player_position_y <= 0:
    response['terminated'] = 'true'
    response['re-entry'] = 'true'
  # End of your code.
  return response
```
#### 2. Make a Environment
Detailed explanations are provided in the following code.
```python
import numpy as np
from tiptoestep.env import Env
from tiptoestep.action import ContinuousAction
from gymnasium import spaces
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import PPO

EXE_FILE = "your_environment_executable_file_path"

action = ContinuousAction(2) # 2-dimensional continuous actions: the first is the force applied along x-axis, and the second is the force applied along z-axis.
action_space = spaces.Box(low=-1.0, high=1.0, shape=(len(action),), dtype=np.float32) # To enable the environment to support the gym.
observation_space = spaces.Box(low=-np.infty, high=np.infty, shape=(12,), dtype=np.float32) # The shape of observation equals the shape of the array returned by transform_fun(obs).
env = Env(pid=0,
            action=action,
            action_space=action_space,
            observation_space=observation_space,
            transform_fun=transform_fun, # The three functions we defined above.
            reward_fun=reward_fun,
            control_fun=control_fun,
            time_scale=1,
            exe_file=EXE_FILE
            )
env = Monitor(env) # Enable the environment to support logging.

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    n_steps=256,
    tensorboard_log="./logs")

model.learn(total_timesteps=100_000)
model.save(f"roller_ball.zip")

env.close() # Ensure the environment is closed.
```