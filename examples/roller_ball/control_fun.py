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