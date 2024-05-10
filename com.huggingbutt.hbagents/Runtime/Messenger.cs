using System;
using System.IO;
using System.IO.MemoryMappedFiles;

// message protocol flag
// 0x01 produced by C#
// 0x02 consumed by C#
// 0x03 produced by Python
// 0x04 consumed by Python
// 0x05 event flag
// 0x06 writing by C#
// 0x07 writing by Python


namespace hbagent
{
    public class Messenger : IDisposable
    {
        private MemoryMappedFile mmf;
        private long size;

        public Messenger(string fileName, long size = 1024 * 16)
        {
            this.size = size;
            mmf = MemoryMappedFile.CreateFromFile(fileName, FileMode.OpenOrCreate, null, size);
        }

        public void Send(Message msg)
        {
            if (mmf == null) throw new Exception("The MemoryMappedFile object has not been instantiated.");
            // Set writing flag
            using (var accessor = mmf.CreateViewAccessor(0, 1))
            {
                accessor.WriteArray<byte>(0, new byte[1] { 0x06 }, 0, 1);
            }

            // Write bytes
            byte[] msgBytes = MessageSerializer.Serialize(msg);
            using (var accessor = mmf.CreateViewAccessor(1, 4 + msgBytes.Length))
            {
                accessor.WriteArray<byte>(0, BitConverter.GetBytes(msgBytes.Length), 0, 4);
                accessor.WriteArray<byte>(4, msgBytes, 0, msgBytes.Length);
            }

            // Set write over flag.
            using (var accessor = mmf.CreateViewAccessor(0, 1))
            {
                accessor.WriteArray<byte>(0, new byte[1] { 0x01 }, 0, 1);
            }
        }

        public Message Receive()
        {
            int dataLength = 0;
            using (var accessor = mmf.CreateViewAccessor(1, 4))
            {
                dataLength = accessor.ReadInt32(0);
            }

            Message msg;
            using (var accessor = mmf.CreateViewAccessor(5, dataLength))
            {
                byte[] msgBytes = new byte[dataLength];
                accessor.ReadArray<byte>(0, msgBytes, 0, dataLength);
                msg = MessageSerializer.Deserialize(msgBytes);
            }

            using (var accessor = mmf.CreateViewAccessor(0, 1)) // Consumed by C#
            {
                accessor.WriteArray<byte>(0, new byte[1] { 0x02 }, 0, 1);
            }

            return msg;
        }

        public bool Check() // Check if the action message has arrived.
        {
            using (var accessor = mmf.CreateViewAccessor(0, 1))
            {
                return accessor.ReadByte(0) == 0x03;
            }
        }

        public void SendReady(uint env_id, uint pid)
        {
            Message msg = new Message();
            msg.pid = pid;
            msg.env_id = env_id;
            msg.agent_id = 0;
            msg.step_id = 0;
            msg.obs_frame_id = 0;
            msg.act_frame_id = 0;
            msg.silent = true;
            msg.message_type = MessageType.Control;
            msg.step_type = StepType.Ready;
            this.Send(msg);
        }

        public void SendEnd(uint env_id, uint pid)
        {
            Message msg = new Message();
            msg.pid = pid;
            msg.env_id = env_id;
            msg.agent_id = 0;
            msg.step_id = 0;
            msg.obs_frame_id = 0;
            msg.act_frame_id = 0;
            msg.silent = true;
            msg.message_type = MessageType.Control;
            msg.step_type = StepType.End;
            this.Send(msg);
        }


        public void Dispose()
        {
            mmf?.Dispose();
        }
    }
}
