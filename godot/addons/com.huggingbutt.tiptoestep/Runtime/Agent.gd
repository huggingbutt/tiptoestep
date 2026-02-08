extends Node
class_name HBAgent

@export var id: int = 0

func pre_collect() -> void:
	pass

func collect() -> Dictionary:
	# Return a dictionary of observations: key -> float/bool
	return {}

func post_collect() -> void:
	pass

func pre_step(cmds: Dictionary) -> void:
	pass

func step(action: Variant) -> void:
	# action: HBContinuousAction or HBCategoricalAction
	pass

func post_step(cmds: Dictionary) -> void:
	pass

func pre_reset(cmds: Dictionary) -> void:
	pass

func reset(cmds: Dictionary) -> void:
	pass

func post_reset(cmds: Dictionary) -> void:
	pass
