extends RefCounted
class_name HBStrDictionarySerializer

static func serialize(dict: Dictionary) -> PackedByteArray:
	var buf := StreamPeerBuffer.new()
	buf.big_endian = false
	for k in dict.keys():
		var v = dict[k]
		var k_bytes: PackedByteArray = str(k).to_utf8_buffer()
		var v_bytes: PackedByteArray = str(v).to_utf8_buffer()
		buf.put_u32(k_bytes.size())
		buf.put_u32(v_bytes.size())
		buf.put_data(k_bytes)
		buf.put_data(v_bytes)
	return buf.data_array

static func deserialize(bytes: PackedByteArray) -> Dictionary:
	var res: Dictionary = {}
	var buf := StreamPeerBuffer.new()
	buf.big_endian = false
	buf.data_array = bytes
	var MAX_KV_BYTES := 1024 * 1024 # 1MB guard
	while buf.get_position() < buf.get_size():
		if buf.get_size() - buf.get_position() < 8:
			push_error("Malformed dict blob: incomplete header")
			break
		var k_len := int(buf.get_u32())
		var v_len := int(buf.get_u32())
		if k_len < 0 or v_len < 0 or (k_len + v_len) > MAX_KV_BYTES:
			push_error("Malformed dict blob: unreasonable kv lengths")
			break
		if buf.get_size() - buf.get_position() < k_len + v_len:
			push_error("Malformed dict blob: truncated data")
			break
		var k_bytes: PackedByteArray = buf.get_data(k_len)
		var v_bytes: PackedByteArray = buf.get_data(v_len)
		var key := k_bytes.get_string_from_utf8()
		var val := v_bytes.get_string_from_utf8()
		res[key] = val
	return res
