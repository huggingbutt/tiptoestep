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

def reward_fun(obs):
    # Write your reward function here.
    # You must return a float number.
    if obs.distance <= 1.42:
        return 1.0
    else:
        return 0.0

    # End of your code.
    # Do not alter the following line, it prevents errors.
    return 0.0

def control_fun(obs) -> Dict[str, str]:
    response = {}

    # Write your code here.
    if obs.distance <= 1.42:
        response['terminated'] = 'true'

    if obs.player_position_y <= 0:
        response['terminated'] = 'true'
        response['re-entry'] = 'true'

    # End of your code.
    return response