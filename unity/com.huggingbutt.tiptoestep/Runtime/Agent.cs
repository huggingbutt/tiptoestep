using System.Collections.Generic;
using UnityEngine;

namespace tiptoestep
{
    public abstract class Agent : MonoBehaviour
    {
        public uint id;

        public virtual void PreStep(Dictionary<string, string> cmds) { }
        public abstract void Step(Action action);
        public virtual void PostStep(Dictionary<string, string> cmds) { }

        public virtual void PreCollect() { }
        public abstract Observation Collect();
        public virtual void PostCollect() { }

        public virtual void PreReset(Dictionary<string, string> cmds) { }
        public abstract void Reset();
        public virtual void PostReset(Dictionary<string, string> cmds) { }

    }
}

