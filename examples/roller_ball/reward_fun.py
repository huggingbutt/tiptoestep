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