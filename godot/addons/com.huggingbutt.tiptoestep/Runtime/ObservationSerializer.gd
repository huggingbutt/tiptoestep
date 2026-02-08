extends RefCounted
class_name HBObservationSerializer

# Wire format per entry:
# [name_len:int32][name_utf8_bytes][type_id:int32][value]
# type_id: 0 = float, 1 = bool
# Only float and bool are supported to match Python observation_to_dict()
static func serialize(obs: Dictionary) -> PackedByteArray:
	var buf := StreamPeerBuffer.new()
	buf.big_endian = false
	for k in obs.keys():
		var v = obs[k]
		var name_bytes: PackedByteArray = str(k).to_utf8_buffer()
		buf.put_32(name_bytes.size())
		buf.put_data(name_bytes)
		if typeof(v) == TYPE_FLOAT:
			buf.put_32(0)
			buf.put_float(float(v))
		elif typeof(v) == TYPE_BOOL:
			buf.put_32(1)
			buf.put_u8(v ? 1 : 0)
		else:
			push_error("HBObservationSerializer: Only float and bool are supported. Key: %s" % [k])
	return buf.data_array
