extends RefCounted
class_name HBMessageSerializer

static func serialize(msg: HBMessage) -> PackedByteArray:
	var buf := StreamPeerBuffer.new()
	buf.big_endian = false
	buf.put_u32(msg.pid)
	buf.put_u32(msg.env_id)
	buf.put_u32(msg.agent_id)
	buf.put_u32(msg.step_id)
	buf.put_u32(msg.obs_frame_id)
	buf.put_u32(msg.act_frame_id)
	buf.put_u8(msg.silent ? 1 : 0)
	buf.put_32(msg.message_type)
	buf.put_32(msg.step_type)
	# Action
	if msg.action == null:
		buf.put_32(0)
	else:
		var act_bytes := HBActionSerializer.serialize(msg.action)
		buf.put_32(act_bytes.size())
		buf.put_data(act_bytes)
	# Cmds
	if msg.cmds == null or msg.cmds.is_empty():
		buf.put_32(0)
	else:
		var dict_bytes := HBStrDictionarySerializer.serialize(msg.cmds)
		buf.put_32(dict_bytes.size())
		buf.put_data(dict_bytes)
	# Observation
	if msg.observation_bytes.is_empty():
		buf.put_32(0)
	else:
		buf.put_32(msg.observation_bytes.size())
		buf.put_data(msg.observation_bytes)
	return buf.data_array

static func deserialize(bytes: PackedByteArray) -> HBMessage:
	var MAX_FRAME_BYTES := 10 * 1024 * 1024
	var buf := StreamPeerBuffer.new()
	buf.big_endian = false
	buf.data_array = bytes
	var msg := HBMessage.new()
	msg.pid = int(buf.get_u32())
	msg.env_id = int(buf.get_u32())
	msg.agent_id = int(buf.get_u32())
	msg.step_id = int(buf.get_u32())
	msg.obs_frame_id = int(buf.get_u32())
	msg.act_frame_id = int(buf.get_u32())
	msg.silent = buf.get_u8() != 0
	msg.message_type = buf.get_32()
	msg.step_type = buf.get_32()
	var act_len := int(buf.get_32())
	if act_len > 0:
		if act_len > MAX_FRAME_BYTES or buf.get_size() - buf.get_position() < act_len:
			push_error("Action blob length out of bounds")
		else:
			var act_bytes: PackedByteArray = buf.get_data(act_len)
			msg.action = HBActionSerializer.deserialize(act_bytes)
	var cmds_len := int(buf.get_32())
	if cmds_len > 0:
		if cmds_len > MAX_FRAME_BYTES or buf.get_size() - buf.get_position() < cmds_len:
			push_error("Cmds blob length out of bounds")
		else:
			var dict_bytes: PackedByteArray = buf.get_data(cmds_len)
			msg.cmds = HBStrDictionarySerializer.deserialize(dict_bytes)
	var obs_len := int(buf.get_32())
	if obs_len > 0:
		if obs_len > MAX_FRAME_BYTES or buf.get_size() - buf.get_position() < obs_len:
			push_error("Observation blob length out of bounds")
		else:
			msg.observation_bytes = buf.get_data(obs_len)
	return msg
