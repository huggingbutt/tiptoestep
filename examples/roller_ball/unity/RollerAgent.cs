using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using tiptoestep;

public class RollerAgent : Agent
{

    public float multipler = 20.0f;
    public Transform target;

    Rigidbody player;

    // Start is called before the first frame update
    void Start()
    {
        player = this.GetComponent<Rigidbody>();
    }

    public override void Step(Action action)
    {
        ContinuousAction continuous = (ContinuousAction)action;
        Vector3 signal = Vector3.zero;
        signal.x = continuous[0];
        signal.z = continuous[1];
        player.AddForce(signal * multipler);
    }

    public override Observation Collect()
    {
        MyObservation obs = new MyObservation();
        obs.target_position_x = target.position.x;
        obs.target_position_y = target.position.y;
        obs.target_position_z = target.position.z;

        obs.player_position_x = this.transform.position.x;
        obs.player_position_y = this.transform.position.y;
        obs.player_position_z = this.transform.position.z;

        obs.player_velocity_x = player.velocity.x;
        obs.player_velocity_y = player.velocity.y;
        obs.player_velocity_z = player.velocity.z;

        obs.player_angular_velocity_x = player.angularVelocity.x;
        obs.player_angular_velocity_y = player.angularVelocity.y;
        obs.player_angular_velocity_z = player.angularVelocity.z;

        obs.distance = Vector3.Distance(target.position, this.transform.position);

        return obs;
    }

    public override void PreReset(Dictionary<string, string> cmds)
    {
        if (cmds.ContainsKey("re-entry") && cmds["re-entry"].Equals("true"))
        {
            this.transform.position = new Vector3(0.0f, 0.5f, 0.0f);
            player.velocity = Vector3.zero;
            player.angularVelocity = Vector3.zero;
        }
    }

    public override void Reset()
    {
        target.position = new Vector3(Random.value * 8 - 4, 0.5f, Random.value * 8 - 4); 
    }
}
