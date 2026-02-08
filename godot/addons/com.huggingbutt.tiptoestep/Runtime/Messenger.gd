extends RefCounted
class_name HBMessenger

var host: String
var port: int
var tcp := StreamPeerTCP.new()
var MAX_FRAME_BYTES := 10 * 1024 * 1024

func _init(_host: String, _port: int) -> void:
	host = _host
	port = _port
	var err := tcp.connect_to_host(host, port)
	if err != OK:
		push_error("HBMessenger connect_to_host failed: %s" % [err])
	# Low-latency small packets
	tcp.set_no_delay(true)

func check() -> bool:
	return tcp.get_available_bytes() > 0

func _read_exact(n: int) -> PackedByteArray:
	var acc := PackedByteArray()
	while acc.size() < n:
		if tcp.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			push_error("HBMessenger socket closed while reading")
			return PackedByteArray()
		var need := n - acc.size()
		var chunk := tcp.get_data(need)
		if chunk.size() == 0:
			# Prevent busy loop; yield to allow more data
			OS.delay_msec(1)
			continue
		acc.append_array(chunk)
	return acc

func send(msg: HBMessage) -> void:
	var payload := HBMessageSerializer.serialize(msg)
	var frame := StreamPeerBuffer.new()
	frame.big_endian = false
	frame.put_u8(0x06)
	frame.put_u32(payload.size())
	frame.put_data(payload)
	frame.put_u8(0x01)
	var data := frame.data_array
	var written := 0
	while written < data.size():
		var slice := data.slice(written, data.size())
		var sent := tcp.put_data(slice)
		if sent == OK:
			written = data.size() # Godot's put_data attempts to write whole buffer when blocking
		else:
			push_error("HBMessenger put_data error: %s" % [sent])
			break


func receive() -> HBMessage:
	var flag := _read_exact(1)
	if flag.size() != 1:
		push_error("HBMessenger failed to read flag")
		return null
	var len_bytes := _read_exact(4)
	if len_bytes.size() != 4:
		push_error("HBMessenger failed to read length")
		return null
	var len_buf := StreamPeerBuffer.new()
	len_buf.big_endian = false
	len_buf.data_array = len_bytes
	var data_len := int(len_buf.get_u32())
	if data_len < 0 or data_len > MAX_FRAME_BYTES:
		push_error("HBMessenger payload length out of bounds: %d" % data_len)
		return null
	var payload := _read_exact(data_len)
	if payload.size() != data_len:
		push_error("HBMessenger truncated payload")
		return null
	var over := _read_exact(1)
	if over.size() != 1:
		push_error("HBMessenger failed to read over flag")
		return null
	# Python-produced frames must be 0x07 ... 0x03
	if int(flag[0]) != 0x07 or int(over[0]) != 0x03:
		push_error("Incorrect data format received from Python: flags %d %d" % [int(flag[0]), int(over[0])])
		return null
	return HBMessageSerializer.deserialize(payload)

func send_ready(env_id: int, pid: int) -> void:
	var msg := HBMessage.new()
	msg.pid = pid
	msg.env_id = env_id
	msg.agent_id = 0
	msg.step_id = 0
	msg.obs_frame_id = 0
	msg.act_frame_id = 0
	msg.silent = true
	msg.message_type = HBMessageType.Control
	msg.step_type = HBStepType.Ready
	send(msg)

func send_end(env_id: int, pid: int) -> void:
	var msg := HBMessage.new()
	msg.pid = pid
	msg.env_id = env_id
	msg.agent_id = 0
	msg.step_id = 0
	msg.obs_frame_id = 0
	msg.act_frame_id = 0
	msg.silent = true
	msg.message_type = HBMessageType.Control
	msg.step_type = HBStepType.End
	send(msg)

func close() -> void:
	if tcp and tcp.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		tcp.disconnect_from_host()
