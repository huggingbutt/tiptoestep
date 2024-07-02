using System;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Net.Sockets;

// message protocol flag
// 0x01 produced by C#
// 0x02 consumed by C#
// 0x03 produced by Python
// 0x04 consumed by Python
// 0x05 event flag
// 0x06 writing by C#
// 0x07 writing by Python


namespace tiptoestep
{
    public class Messenger : IDisposable
    {
        private MemoryMappedFile mmf;
        private long size;
        private TcpClient client;
        private NetworkStream stream;

        public Messenger(string host, string port, long size = 1024 * 16)
        {
            this.size = size;
            try
            {
                client = new TcpClient(host, int.Parse(port));
                stream = client.GetStream();
            }
            catch (ArgumentNullException e)
            {
                Console.WriteLine($"ArgumentNullException: {e}");
            }
            catch (SocketException e)
            {
                Console.WriteLine($"SocketException: {e}");
            }
        }

        public void Send(Message msg)
        {
            using (var stream = new MemoryStream())
            {
                using (var writer = new BinaryWriter(stream))
                {
                    writer.Write((byte)0x06); ; // Set writing flag
                    byte[] msgBytes = MessageSerializer.Serialize(msg);
                    writer.Write(BitConverter.GetBytes(msgBytes.Length));
                    
                    writer.Write(msgBytes);
                    writer.Write((byte)0x01); // Set write over flag.
                }
                byte[] send_data = stream.ToArray();
                this.stream.Write(send_data);
            }

        }

        public Message Receive()
        {
            byte[] flag = new byte[1];
            this.stream.Read(flag, 0, 1);

            byte[] dataLengthBytes = new byte[4];
            this.stream.Read(dataLengthBytes, 0, 4);
            int dataLength = BitConverter.ToInt32(dataLengthBytes);

            byte[] msgBytes = new byte[dataLength];
            this.stream.Read(msgBytes, 0, dataLength);

            byte[] overFlag = new byte[1];
            this.stream.Read(overFlag, 0, 1);

            Message msg = null;
            if (flag[0] != 0x07 || overFlag[0] != 0x03) throw new Exception("Incorrect data format received from Python.");
            msg = MessageSerializer.Deserialize(msgBytes);
            return msg;
        }

        public bool Check() // Check if the action message has arrived.
        {
            return this.stream.DataAvailable;
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
            this.stream.Dispose();
            this.stream.Close();
            this.client.Dispose();
            this.client.Close();
        }
    }
}
