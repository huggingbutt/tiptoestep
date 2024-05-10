using System;
using System.IO;
using System.Reflection;
using System.Text;

namespace hbagent
{
    public class Observation
    {
        private byte[] _bytes;

        public Observation() { }
        public Observation(byte[] bytes)
        {
            this._bytes = bytes;
        }

        public byte[] GetBytes()
        {
            if (this._bytes == null) throw new Exception("Execute SerializeToBytes() first.");
            return this._bytes;
        }

        public void SetBytes(byte[] bytes)
        {
            this._bytes = bytes;
        }

        public void SerializeToBytes()
        {
            if (this._bytes != null) return;
            PropertyInfo[] properties = this.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
            using (var stream = new MemoryStream())
            {
                using (var writer = new BinaryWriter(stream))
                {
                    foreach (var property in properties)
                    {
                        string pname = property.Name;
                        writer.Write(pname.Length);
                        writer.Write(Encoding.UTF8.GetBytes(pname));

                        if (property.PropertyType == typeof(float))
                        {
                            writer.Write(0);
                            float value = (float)property.GetValue(this);
                            writer.Write(value);
                        }
                        else if (property.PropertyType == typeof(bool))
                        {
                            writer.Write(1);
                            bool value = (bool)property.GetValue(this);
                            writer.Write(value);
                        }
                        else
                        {
                            throw new Exception("The properties of Observation class support only 'float' and 'bool' data type.");
                        }
                    }
                }
                this._bytes = stream.ToArray();
            }
        }

        public static T Deserialize<T>(byte[] bytes) where T : new()
        {
            using (var stream = new MemoryStream(bytes))
            {
                using (var reader = new BinaryReader(stream))
                {
                    var result = new T();
                    foreach (var prop in typeof(T).GetProperties())
                    {
                        if (prop.PropertyType == typeof(float))
                        {
                            float value = reader.ReadSingle();
                            prop.SetValue(result, value);
                        }
                        else if (prop.PropertyType == typeof(bool))
                        {
                            bool value = reader.ReadBoolean();
                            prop.SetValue(result, value);
                        }
                    }

                    return result;
                }
            }
        }
    }
}

