extends Node
class_name HBEnv

@export var pid: int = 0
@export var env_id: int = 0
@export var host: String = "127.0.0.1"
@export var port: int = 10086
@export var agent_path: NodePath

var messenger: HBMessenger
var agent: HBAgent

var action_frame_count: int = 0
var step_count: int = 0
var render_flag: bool = false
var temp_msg: HBMessage

func _parse_cmd_args() -> void:
	var args := OS.get_cmdline_args()
	for arg in args:
		if arg.begins_with("-pid="):
			pid = int(arg.substr(5))
		elif arg.begins_with("-env_id="):
			env_id = int(arg.substr(8))
		elif arg.begins_with("-host="):
			host = arg.substr(6)
		elif arg.begins_with("-port="):
			port = int(arg.substr(6))

func _ready() -> void:
	_parse_cmd_args()
	if agent_path != NodePath():
		agent = get_node(agent_path) as HBAgent
	if agent == null:
		push_warning("HBEnv: agent is null; please assign an HBAgent node")
	messenger = HBMessenger.new(host, port)
	# Send Ready control
	messenger.send_ready(env_id, pid)

func _collect_observation(act_frame_id: int) -> void:
	if agent == null:
		return
	agent.pre_collect()
	var obs: Dictionary = agent.collect()
	agent.post_collect()
	var msg := HBMessage.new()
	msg.pid = pid
	msg.env_id = env_id
	msg.agent_id = agent.id if agent != null else 0
	msg.message_type = HBMessageType.Observation
	msg.step_type = HBStepType.Step
	msg.step_id = step_count
	step_count += 1
	msg.act_frame_id = act_frame_id
	msg.obs_frame_id = Engine.get_physics_frames()
	msg.observation_bytes = HBObservationSerializer.serialize(obs)
	messenger.send(msg)

func _physics_process(_delta: float) -> void:
	if render_flag:
		_collect_observation(action_frame_count)
		render_flag = false
	else:
		if not messenger.check():
			# no incoming action/control yet
			pass
		else:
			var action_msg := messenger.receive()
			temp_msg = action_msg
			if action_msg == null:
				return
			if action_msg.message_type == HBMessageType.Action and action_msg.step_type == HBStepType.Step:
				render_flag = true
				if agent != null:
					agent.pre_step(action_msg.cmds)
					agent.step(action_msg.action)
					agent.post_step(action_msg.cmds)
			elif action_msg.message_type == HBMessageType.Control and action_msg.step_type == HBStepType.Reset:
				if agent != null:
					agent.pre_reset(action_msg.cmds)
					agent.reset(action_msg.cmds)
					agent.post_reset(action_msg.cmds)
				step_count = 0
				_collect_observation(action_frame_count)
				render_flag = false
			elif action_msg.message_type == HBMessageType.Control and action_msg.step_type == HBStepType.End:
				get_tree().quit()
	action_frame_count += 1

func _exit_tree() -> void:
	if messenger != null:
		messenger.close()
