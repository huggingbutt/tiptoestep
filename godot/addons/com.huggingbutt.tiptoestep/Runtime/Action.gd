extends RefCounted
class_name HBAction

# Continuous action
class HBContinuousAction:
	extends RefCounted
	var values: PackedFloat32Array
	func _init(count: int = 0):
		values = PackedFloat32Array()
		values.resize(count)

# Categorical action of ints only for now (to mirror current Python/Unity)
class HBCategoricalAction:
	extends RefCounted
	var all_actions: PackedInt32Array
	var value: int = 0
	func _init(actions: PackedInt32Array = PackedInt32Array()):
		all_actions = actions

class HBActionSerializer:
	extends RefCounted
	static func serialize(action: Variant) -> PackedByteArray:
		var buf := StreamPeerBuffer.new()
		buf.big_endian = false
		if action is HBContinuousAction:
			buf.put_u8(0) # type indicator
			buf.put_u32(action.values.size())
			for v in action.values:
				buf.put_float(v)
			return buf.data_array
		elif action is HBCategoricalAction:
			buf.put_u8(1) # type indicator
			buf.put_u32(action.all_actions.size())
			for v in action.all_actions:
				buf.put_u32(v)
			buf.put_u32(action.value)
			return buf.data_array
		else:
			push_error("Unsupported action type for serialization")
			return PackedByteArray()

	static func deserialize(bytes: PackedByteArray) -> Variant:
		var buf := StreamPeerBuffer.new()
		buf.big_endian = false
		buf.data_array = bytes
		var type_indicator := int(buf.get_u8())
		if type_indicator == 0:
			var length := int(buf.get_u32())
			var act := HBContinuousAction.new(length)
			for i in range(length):
				act.values[i] = buf.get_float()
			return act
		elif type_indicator == 1:
			var count := int(buf.get_u32())
			var values := PackedInt32Array()
			values.resize(count)
			for i in range(count):
				values[i] = int(buf.get_u32())
			var selected := int(buf.get_u32())
			var act2 := HBCategoricalAction.new(values)
			act2.value = selected
			return act2
		else:
			push_error("Unknown action type indicator")
			return null
