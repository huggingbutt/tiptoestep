extends RefCounted
class_name HBMessage

var pid: int = 0
var env_id: int = 0
var agent_id: int = 0
var step_id: int = 0
var obs_frame_id: int = 0
var act_frame_id: int = 0
var silent: bool = false
var message_type: int = 0 # HBMessageType
var step_type: int = 2    # HBStepType.Step
var action: Variant = null # HBContinuousAction | HBCategoricalAction | null
var cmds: Dictionary = {}
var observation_bytes: PackedByteArray = PackedByteArray() # wire-ready bytes
