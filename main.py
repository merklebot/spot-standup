import os

ROBOT_IP="192.168.6.9"#os.environ['ROBOT_IP']
SPOT_USERNAME="admin"#os.environ['SPOT_USERNAME']
SPOT_PASSWORD="2zqa8dgw7lor"#os.environ['SPOT_PASSWORD']


import bosdyn.client
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand
from bosdyn.client.robot_command import RobotCommandBuilder
from bosdyn.geometry import EulerZXY
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive

import time

def main():
    sdk = bosdyn.client.create_standard_sdk('LessonOneClient')
    # Create instance of robot and auth with credentials
    robot = sdk.create_robot(ROBOT_IP)
    robot.authenticate(SPOT_USERNAME, SPOT_PASSWORD)

    # Setup and release E-Stop
    estop_client = robot.ensure_client(EstopClient.default_service_name)
    estop_endpoint = EstopEndpoint(estop_client, 'GNClient', 9.0)
    estop_endpoint.force_simple_setup()
    estop_keepalive = EstopKeepAlive(estop_endpoint)


    # Create lease client and take exclusive control over Spot.
    lease_client = robot.ensure_client('lease')
    lease = lease_client.take()
    lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(lease_client)
    # Try to power on the robot
    robot.power_on(timeout_sec=20)
    if robot.is_powered_on():
        print("Powered On")
            # If everything went smooth, Spot face lights should turn green
    else:
            # In case of some problems, e.g. somebody stole control over robot
        print("Failed")
        exit(0)
    # Synchronize Spor inner time with ours - to avoid outdated commands
    robot.time_sync.wait_for_sync()
    # To execute robot movement, create command client through which orders are sent
    command_client = robot.ensure_client(RobotCommandClient.default_service_name)
    # Start movement with simple stand up
    blocking_stand(command_client, timeout_sec=10)
    # Rotate robot body:
    #  1. Build command for body rotation. It’s not an easy task to control robot motion with commands on low level.
    #     Bosdyn Client allow as to use a shortcut - RobotCommandBuilder. It contains a number of predefined commands,
    #     you need just to choose one of your liking and insert parameters
    footprint_R_body = EulerZXY(yaw=0.1, roll=0.1, pitch=0.1)
    cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body)
    #  2. Execute builded command
    command_client.robot_command(cmd)
    time.sleep(2)
    # Return robot state back
    command_client.robot_command(RobotCommandBuilder.synchro_stand_command(footprint_R_body=EulerZXY(yaw=0, roll=0, pitch=0)))
    time.sleep(2)
    # Change robot height
    cmd = RobotCommandBuilder.synchro_stand_command(body_height=0.1)
    command_client.robot_command(cmd)
    time.sleep(5)
    robot.power_off(cut_immediately=False)

    time.sleep(1)

    # Return lease
    lease_client.return_lease(lease)
    lease_keep_alive.shutdown()

    # Set E-Stop back
    try:
        estop_keepalive.stop()
    except:
        self.robot.logger.error("Failed to set estop")
        traceback.print_exc()
    estop_keepalive.shutdown()

if __name__=='__main__':
    main()