using tiptoestep;

public class MyObservation : Observation
{
    // Target information
    public float target_position_x { get; set; }
    public float target_position_y { get; set; }
    public float target_position_z { get; set; }

    // Player infromation
    public float player_position_x { get; set; }
    public float player_position_y { get; set; }
    public float player_position_z { get; set; }

    public float player_velocity_x { get; set; }
    public float player_velocity_y { get; set; }
    public float player_velocity_z { get; set; }

    public float player_angular_velocity_x { get; set; }
    public float player_angular_velocity_y { get; set; }
    public float player_angular_velocity_z { get; set; }

    public float distance { get; set; }
}
