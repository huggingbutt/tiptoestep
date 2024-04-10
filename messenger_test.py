from hbagent.messenger import Messenger, MessageSerializer
from hbagent.action import ContinuousAction
if __name__ == '__main__':
    filename = "/Users/admin/.cache/hbagent/0_1.mmf"
    messenger = Messenger(filename, pid=0, env_id=1)
    messenger.is_ready()

    action = ContinuousAction(3)
    action[0] = 0
    action[1] = 1
    action[2] = 0

    messenger.send_control(agent_id=0, step_id=0, signal='reset')
    messenger.send_action(agent_id=0, step_id=0, action=action)
    while not messenger.check():
        pass

    msg = messenger.receive()