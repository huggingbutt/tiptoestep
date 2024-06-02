using System;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
#if UNITY_EDITOR
using UnityEditor;
#endif
using UnityEngine.UI;

namespace tiptoestep
{
    public class Env : MonoBehaviour
    {
        public uint pid;
        public uint env_id;
        public string debug_mmf;
        public Text textPlaceholder;
        bool renderFlag = false;
        private Message tempMsg; // todo? For all 'PostXXXX' function. 

        Messenger messenger;
        public Agent agent;

        string mmf;
        int actionFrameCount = 0;
        uint stepCount = 0;

        Dictionary<string, string> ParseCommand(string[] arguments)
        {
            Dictionary<string, string> args = new Dictionary<string, string>();
            for (int i = 0; i < arguments.Length; i++)
            {
                string arg = arguments[i];
                if (arg.StartsWith("-pid="))
                {
                    args["pid"] = arg.Substring(3 + 2);
                }
                if (arg.StartsWith("-env_id="))
                {
                    args["env_id"] = arg.Substring(6 + 2);
                }
                if (arg.StartsWith("-time_scale="))
                {
                    args["time_scale"] = arg.Substring(10 + 2);
                }
                if (arg.StartsWith("-mmf="))
                {
                    args["mmf"] = arg.Substring(3 + 2);
                }
            }
            return args;
        }

        private void Awake()
        {
            Physics.simulationMode = SimulationMode.Script;
#if UNITY_EDITOR 
            // 
            if (this.debug_mmf != null && this.debug_mmf.Length > 0)
                this.mmf = this.debug_mmf;
            else
                throw new Exception("'mmf' file cannot be empty during execution in Editor.");

#else

            string[] args = Environment.GetCommandLineArgs();
            Dictionary<string, string> arguments = ParseCommand(args);
            if (arguments.Count <= 0
                || !arguments.ContainsKey("pid")
                || !arguments.ContainsKey("env_id")
                || !arguments.ContainsKey("mmf")
                ) throw new ArgumentException("Startup argument error");

            if (arguments.ContainsKey("time_scale"))
            {
                Time.timeScale = float.Parse(arguments["time_scale"]);
            }

            this.pid = uint.Parse(arguments["pid"]);
            this.env_id = uint.Parse(arguments["env_id"]);
            this.mmf = arguments["mmf"];

#endif
            
            messenger = new Messenger(this.mmf);
        }

        void WriteToLogFile(string message)
        {
            DateTime now = DateTime.Now;
            string timestamp = now.ToString("yyyy-MM-dd HH:mm:ss.fff");
            string path = Path.Combine(Application.dataPath.Split("Contents")[0], "log.txt");
            StreamWriter writer = new StreamWriter(path, true);
            writer.WriteLine($"{timestamp} -- {message}");
            writer.Close();
        }

        // Start is called before the first frame update
        void Start()
        {
#if LOG_TO_FILE
            WriteToLogFile($"{this.pid}_{this.env_id} Sending ready.");
#endif
            this.messenger.SendReady(this.env_id, this.pid);
#if LOG_TO_FILE
            WriteToLogFile($"{this.pid}_{this.env_id} Sent ready.");
#endif
        }


        void CollectObservation(int actFrameId)
        {
            Message msg = new Message();
            msg.pid = this.pid;
            msg.env_id = this.env_id;
            msg.agent_id = this.agent.id;
            msg.message_type = MessageType.Observation;
            msg.step_type = StepType.Step;

            msg.step_id = this.stepCount++;
            msg.act_frame_id = (uint)actFrameId;
            msg.obs_frame_id = (uint)Time.frameCount;

            this.agent.PreCollect();
            msg.observation = this.agent.Collect();
            this.agent.PostCollect();

            this.messenger.Send(msg);

        }

        private void FixedUpdate()
        {
            if (this.renderFlag)
            {
                Physics.Simulate(Time.fixedDeltaTime);
                CollectObservation(actionFrameCount);
                this.renderFlag = false;
            }
            else
            {
                if (!this.messenger.Check()) return; // Waiting for action message from Python
                Message actionMsg = this.messenger.Receive(); // Consume action message
                                                              // and set flag 0x02 indicates taht message has received by C#
                this.tempMsg = actionMsg;
                if (actionMsg.message_type == MessageType.Action
                    && actionMsg.step_type == StepType.Step)
                {
                    renderFlag = true;
                    this.agent.PreStep(actionMsg.cmds);
                    this.agent.Step(actionMsg.action);
                    this.agent.PostStep(actionMsg.cmds); // The term 'Post' in the function name 'PostStep' may cause confusion.
                                                         // Does executing the 'PostStep' function after the 'Step' function mean
                                                         // it occurs after one step of physical simulation?
                }

                if (actionMsg.message_type == MessageType.Control
                    && actionMsg.step_type == StepType.Reset)
                {
                    //Debug.Log(actionMsg.cmds);
                    this.agent.PreReset(actionMsg.cmds);
                    this.agent.Reset();
                    this.agent.PostReset(actionMsg.cmds);
                    this.stepCount = 0;
                    CollectObservation(this.actionFrameCount);
                    renderFlag = false;
                }

                if (actionMsg.message_type == MessageType.Control
                    && actionMsg.step_type == StepType.End)
                {
#if UNITY_EDITOR
                    EditorApplication.isPlaying = false;
#endif
                    Application.Quit();
                }
            }
            actionFrameCount++;
        }

        private void OnApplicationQuit()
        {
            if (this.messenger != null) this.messenger?.Dispose();
        }

    }

}
