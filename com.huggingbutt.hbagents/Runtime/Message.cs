using System;
using System.Collections.Generic;
using System.IO;

namespace hbagent
{
    public class Message
    {
        public uint pid { set; get; }
        public uint env_id { set; get; }
        public uint agent_id { set; get; }
        public uint step_id { set; get; }
        public uint obs_frame_id { set; get; }
        public uint act_frame_id { set; get; }
        public bool silent { set; get; }
        public MessageType message_type { set; get; }
        public StepType step_type { set; get; }
        public Action action { set; get; }
        public Dictionary<string, string> cmds { set; get; }
        public Observation observation { set; get; }
    }


    public static class MessageSerializer
    {
        public static byte[] Serialize(Message msg)
        {
            using (var stream = new MemoryStream())
            {
                using (var writer = new BinaryWriter(stream))
                {
                    writer.Write(msg.pid); // 4 bytes
                    writer.Write(msg.env_id);
                    writer.Write(msg.agent_id);
                    writer.Write(msg.step_id);
                    writer.Write(msg.obs_frame_id);
                    writer.Write(msg.act_frame_id);
                    writer.Write(msg.silent); // one byte
                    writer.Write((int)msg.message_type);
                    writer.Write((int)msg.step_type);


                    // Action
                    if (msg.action == null)
                    {
                        writer.Write(0);
                    }
                    else
                    {
                        byte[] action_ = ActionSerializer.Serialize(msg.action);
                        //Debug.Log($"action length {action_.Length}");
                        writer.Write(action_.Length);
                        writer.Write(action_);
                    }

                    // Dictionary
                    if (msg.cmds == null)
                    {
                        writer.Write(0);
                    }
                    else
                    {
                        byte[] cmds_ = StrDictionarySerializer.Serialize(msg.cmds);
                        //Debug.Log($"cmds_ length {cmds_.Length}");
                        writer.Write(cmds_.Length);
                        writer.Write(cmds_);
                    }

                    // Observation
                    if (msg.observation == null)
                    {
                        writer.Write(0);
                    }
                    else
                    {
                        msg.observation.SerializeToBytes();
                        byte[] obs_ = msg.observation.GetBytes();
                        //Debug.Log($"obs length {obs_.Length}");
                        writer.Write(obs_.Length);
                        writer.Write(obs_);
                    }

                    return stream.ToArray();
                }
            }
        }

        public static Message Deserialize(byte[] bytes)
        {
            using (var stream = new MemoryStream(bytes))
            {
                using (var reader = new BinaryReader(stream))
                {
                    Message msg = new Message();
                    // Int32
                    msg.pid = reader.ReadUInt32();
                    msg.env_id = reader.ReadUInt32();
                    msg.agent_id = reader.ReadUInt32();
                    msg.step_id = reader.ReadUInt32();
                    msg.obs_frame_id = reader.ReadUInt32();
                    msg.act_frame_id = reader.ReadUInt32();

                    // Boolean
                    msg.silent = reader.ReadBoolean();

                    // Enum
                    msg.message_type = (MessageType)Enum.ToObject(typeof(MessageType), reader.ReadInt32());
                    msg.step_type = (StepType)Enum.ToObject(typeof(StepType), reader.ReadInt32());

                    // Action bytes length
                    int act_len = reader.ReadInt32();
                    if (act_len > 0) msg.action = ActionSerializer.Deserialize(reader.ReadBytes(act_len));

                    // Cmds bytes length
                    int cmds_len = reader.ReadInt32();
                    if (cmds_len > 0)
                        msg.cmds = StrDictionarySerializer.Deserialize(reader.ReadBytes(cmds_len));
                    else
                        msg.cmds = new Dictionary<string, string>(){ };

                    // Observation bytes length
                    int obs_len = reader.ReadInt32();
                    if (obs_len > 0)
                    {
                        msg.observation = new Observation(reader.ReadBytes(obs_len));
                    }

                    return msg;
                }
            }
        }

        public static string MessageToStr(Message msg)
        {
            StringWriter sw = new StringWriter();
            sw.WriteLine($"pid: {msg.pid}");
            sw.WriteLine($"env_id: {msg.env_id}");
            sw.WriteLine($"agent_id: {msg.agent_id}");
            sw.WriteLine($"step_id: {msg.step_id}");
            sw.WriteLine($"act_frame_id: {msg.act_frame_id}");
            sw.WriteLine($"obs_frame_id: {msg.obs_frame_id}");
            sw.WriteLine($"silent: {msg.silent}");
            sw.WriteLine($"message_type: {msg.message_type}");
            sw.WriteLine($"step_type: {msg.step_type}");
            sw.WriteLine($"cmds: {msg.cmds}");
            sw.WriteLine($"action: {msg.action}");
            string msgStr = sw.ToString();
            sw.Close();
            return msgStr;
        }
    }
}


