using System;

namespace tiptoestep
{
    public class ContinuousAction : Action
    {
        private float[] data;

        public ContinuousAction(int num)
        {
            data = new float[num];
        }

        public float this[int index]
        {
            get
            {
                // Include validation if necessary
                if (index < 0 || index >= data.Length)
                    throw new IndexOutOfRangeException("Index out of range");

                return data[index];
            }
            set
            {
                // Include validation if necessary
                if (index < 0 || index >= data.Length)
                    throw new IndexOutOfRangeException("Index out of range");

                data[index] = value;
            }
        }

        public float[] Value
        {
            get { return data; }
            set { data = value; }
        }

        public int Length
        {
            get { return this.data.Length; }
        }


    }
}

