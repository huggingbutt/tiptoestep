using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace tiptoestep
{
    public static class StrDictionarySerializer
    {
        public static byte[] Serialize(Dictionary<string, string> dictionary)
        {
            using (var ms = new MemoryStream())
            {
                foreach (var kvp in dictionary)
                {
                    // Convert key and value to bytes
                    var keyBytes = Encoding.UTF8.GetBytes(kvp.Key);
                    var valueBytes = Encoding.UTF8.GetBytes(kvp.Value);

                    // Write the length of the key and value to ensure proper deserialization
                    ms.Write(BitConverter.GetBytes(keyBytes.Length), 0, 4);
                    ms.Write(BitConverter.GetBytes(valueBytes.Length), 0, 4);

                    // Write the actual key and value bytes
                    ms.Write(keyBytes, 0, keyBytes.Length);
                    ms.Write(valueBytes, 0, valueBytes.Length);
                }

                return ms.ToArray();
            }
        }

        public static Dictionary<string, string> Deserialize(byte[] byteArray)
        {
            var dictionary = new Dictionary<string, string>();

            using (var ms = new MemoryStream(byteArray))
            {
                while (ms.Position < ms.Length)
                {
                    // Read lengths of the key and value
                    var keyLengthBytes = new byte[4];
                    var valueLengthBytes = new byte[4];
                    ms.Read(keyLengthBytes, 0, 4);
                    ms.Read(valueLengthBytes, 0, 4);

                    var keyLength = BitConverter.ToInt32(keyLengthBytes, 0);
                    var valueLength = BitConverter.ToInt32(valueLengthBytes, 0);

                    // Read the key and value bytes
                    var keyBytes = new byte[keyLength];
                    var valueBytes = new byte[valueLength];
                    ms.Read(keyBytes, 0, keyLength);
                    ms.Read(valueBytes, 0, valueLength);

                    // Convert bytes back to strings and add to the dictionary
                    var key = Encoding.UTF8.GetString(keyBytes);
                    var value = Encoding.UTF8.GetString(valueBytes);
                    dictionary.Add(key, value);
                }
            }

            return dictionary;
        }
    }
}