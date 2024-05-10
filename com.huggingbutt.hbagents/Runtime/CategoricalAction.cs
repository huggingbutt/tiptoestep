using System;
using System.Collections.Generic;
using System.Linq;

namespace hbagent
{
    public class CategoricalAction<T> : Action
    {
        private HashSet<T> _values = new HashSet<T>();
        private T _value;

        public CategoricalAction() { }

        public CategoricalAction(params T[] values)
        {
            foreach (T value in values)
            {
                this._values.Add(value);
            }
        }

        public void SetAllActions(params T[] actions)
        {
            this._values = new HashSet<T>(actions);
        }

        public T[] GetAllActions()
        {
            return this._values.ToArray<T>();
        }

        public void AddAction(T action)
        {
            this._values.Add(action);
        }


        public T Value
        {
            get => this._value;
            set
            {
                // Check if object is in list
                if (!this._values.Contains(value))
                {
                    throw new ArgumentException($"Value must be in [{String.Join(",", this._values)}]");
                }
                this._value = value;
            }
        }

        public string GetValueType()
        {
            return typeof(T).Name;
        }
    }
}
