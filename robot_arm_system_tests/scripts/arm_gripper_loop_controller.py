#!/usr/bin/env python3
"""
Control robot arm and gripper to perform movements between positions.

This script creates a ROS 2 node that moves a robot arm between target and home positions,
coordinating with gripper actions (open/close) at each position. The movement happens
in a continuous loop.

Action Clients:
    /arm_controller/follow_joint_trajectory (control_msgs/FollowJointTrajectory):
        Commands for controlling arm joint positions
    
    /gripper_action_controller/gripper_cmd (control_msgs/GripperCommand):
        Commands for opening and closing the gripper
"""

import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory, GripperCommand
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class ArmGripperLoopController(Node):
  

    def __init__(self):
      
        super().__init__('arm_gripper_loop_controller')

        # Set up arm trajectory action client for arm movement control
        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory'
        )

        # Set up gripper action client for gripper control
        self.gripper_client = ActionClient(
            self,
            GripperCommand,
            '/gripper_action_controller/gripper_cmd'
        )

        # Wait for both action servers to be available
        self.get_logger().info('Waiting for action servers...')
        self.arm_client.wait_for_server()
        self.gripper_client.wait_for_server()
        self.get_logger().info('Action servers connected!')

        # List of joint names for the robot arm
        self.joint_names = [
            'link1_to_link2', 'link2_to_link3', 'link3_to_link4',
            'link4_to_link5', 'link5_to_link6', 'link6_to_link6_flange'
        ]

        # Define target and home positions for the arm
        self.target_pos = [1.345, -1.23, 0.264, -0.296, 0.389, -1.5]
        self.home_pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Create timer that triggers the control loop quickly after start (0.1 seconds)
        self.create_timer(0.1, self.control_loop_callback)

    def send_arm_command(self, positions: list) -> None:
     
        # Create a trajectory point with the target positions
        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start = Duration(sec=2)  # Allow 2 seconds for movement

        # Create and send the goal message
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        goal_msg.trajectory.points = [point]

        self.arm_client.send_goal_async(goal_msg)

    def send_gripper_command(self, position: float) -> None:
       
        # Create and send the gripper command
        goal_msg = GripperCommand.Goal()
        goal_msg.command.position = position
        goal_msg.command.max_effort = 5.0

        self.gripper_client.send_goal_async(goal_msg)

    def control_loop_callback(self) -> None:

        # Move to target position
        self.get_logger().info('Moving to target position')
        self.send_arm_command(self.target_pos)
        time.sleep(2.5)  # Wait for arm to reach target (2.5s)

        # Pause at target position
        self.get_logger().info('Reached target position - Pausing')
        time.sleep(1.0)  # Pause for 1 second at target

        # Close gripper
        self.get_logger().info('Closing gripper')
        self.send_gripper_command(-0.7)  # Close gripper
        time.sleep(0.5)  # Wait for gripper to close

        # Move to home position
        self.get_logger().info('Moving to home position')
        self.send_arm_command(self.home_pos)
        time.sleep(2.5)  # Wait for arm to reach home (2.5s)

        # Pause at home position
        self.get_logger().info('Reached home position - Pausing')
        time.sleep(1.0)  # Pause for 1 second at home

        # Open gripper
        self.get_logger().info('Opening gripper')
        self.send_gripper_command(0.0)  # Open gripper
        time.sleep(0.5)  # Wait for gripper to open

        # Final pause before next cycle
        time.sleep(1.0)


def main(args=None):
 
    rclpy.init(args=args)
    controller = ArmGripperLoopController()

    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        controller.get_logger().info('Shutting down arm gripper controller...')
    finally:
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()