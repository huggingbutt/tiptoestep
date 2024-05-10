using System;
using System.IO;
using System.Text;

namespace hbagent
{
    public class Action
    {

    }

    public static class ActionSerializer
    {
        public static byte[] Serialize(Action action)
        {
            using (var stream = new MemoryStream())
            {
                using (var writer = new BinaryWriter(stream, Encoding.UTF8))
                {
                    switch (action)
                    {
                        case ContinuousAction continuousAction:
                            writer.Write((byte)0); // Type indicator for ContinuousAction
                            writer.Write(continuousAction.Length);
                            foreach (var value in continuousAction.Value)
                            {
                                writer.Write(value);
                            }
                            break;
                        case CategoricalAction<int> categoricalAction: // Example for int, extend for other types
                            writer.Write((byte)1); // Type indicator for CategoricalAction<int>
                            var allActions = categoricalAction.GetAllActions();
                            writer.Write(allActions.Length);
                            foreach (var actionValue in allActions)
                            {
                                writer.Write(actionValue);
                            }
                            writer.Write(categoricalAction.Value);
                            break;
                            // Add more cases here for other specific types
                    }
                }

                return stream.ToArray();
            }
        }

        public static Action Deserialize(byte[] bytes)
        {
            using (var stream = new MemoryStream(bytes))
            {
                using (var reader = new BinaryReader(stream, Encoding.UTF8))
                {
                    var typeIndicator = reader.ReadByte();
                    switch (typeIndicator)
                    {
                        case 0: // ContinuousAction
                            var length = reader.ReadInt32();
                            var continuousAction = new ContinuousAction(length);
                            for (int i = 0; i < length; i++)
                            {
                                continuousAction[i] = reader.ReadSingle();
                            }
                            return continuousAction;
                        case 1: // CategoricalAction<int>, example for int
                            var count = reader.ReadInt32();
                            var values = new int[count];
                            for (int i = 0; i < count; i++)
                            {
                                values[i] = reader.ReadInt32();
                            }
                            var value = reader.ReadInt32();
                            var categoricalAction = new CategoricalAction<int>(values) { Value = value };
                            return categoricalAction;
                            // Add more cases here for other specific types
                    }
                }
                return null;
            }
        }

        public static Action Deserialize2<T>(byte[] bytes) where T : new()
        {
            using (var stream = new MemoryStream(bytes))
            {
                using (var reader = new BinaryReader(stream, Encoding.UTF8))
                {
                    var typeIndicator = reader.ReadByte();
                    switch (typeIndicator)
                    {
                        case 0: // ContinuousAction
                            var length = reader.ReadInt32();
                            var continuousAction = new ContinuousAction(length);
                            for (int i = 0; i < length; i++)
                            {
                                continuousAction[i] = reader.ReadSingle();
                            }
                            return continuousAction;
                        case 1: // CategoricalAction<int>, example for int
                            var count = reader.ReadInt32();
                            var values = new int[count];
                            for (int i = 0; i < count; i++)
                            {
                                values[i] = reader.ReadInt32();
                            }
                            var value = reader.ReadInt32();
                            var categoricalAction = new CategoricalAction<int>(values) { Value = value };
                            return categoricalAction;
                            // Add more cases here for other specific types
                    }
                }
                return null;
            }
        }
    }
}

