#!/usr/bin/env python3

#~/ardupilot/Tools/autotest/sim_vehicle.py --vehicle=ArduSub --aircraft="bwsibot" -L RATBeach --out=udp:YOUR_COMPUTER_IP:14550
#ros2 launch mavros apm.launch fcu_url:=udp://192.168.2.2:14550@14555 gcs_url:=udp://:14550@YOUR_COMPUTER_IP:14550 tgt_system:=1 tgt_component:=1 system_id:=255 component_id:=240

#cd ~/auvc_ws
#colcon build --packages-select intro_to_ros --symlink-install
#source ~/auvc_ws/install/setup.zsh

#ros2 topic list
#ros2 topic type /your/topic
#ro2 topic echo /your/topic :)))))
#ros2  interface show your_msg_library/msg/YourMessageType
import rclpy
from rclpy.node import Node
from mavros_msgs.msg import ManualControl, Altitude
import numpy as np
import time

import matplotlib as plt


class PIDNode(Node):
    def __init__(self):
        super().__init__('move_node')

        self.move_publisher = self.create_publisher(
            ManualControl,
            'bluerov2/manual_control',
            10
        )
        self.depth_subscriber = self.create_subscription(
            Altitude,
            'bluerov2/depth',
            self.depth_callback,
            10
        )

        self.desired_depth_subscriber = self.create_subscription(
            Altitude,
            'bluerov2/desired_depth',
            self.desired_depth_callback,
            10
        )
        """
        PID CONSTANTS
        """
        self.kp = 55
        self.ki = 7
        self.kd = 15
        self.max_integral = 4.0
        self.min_output = -50.0
        self.max_output = 50.0
        self.integral = 0.0
        self.previous_error = 0.0
        """"""
        self.get_logger().info('starting publisher node')
        #self.pid_yaw = PIDController(0.5, 0.1, 0.05, 1.0, -50, 50)
        self.depth = float()
        self.desired_depth = None
        self.prev_time = time.time()


    def reset(self):
        self.integral = 0.0
        self.previous_error = 0.0
        self.prev_time = time.time()

    def compute(self, error, dt):
        self.integral += error*dt
        self.integral = max(min(self.integral, self.max_integral), -self.max_integral)

        derivative = (error - self.previous_error) / dt

        proportional = self.kp * error
        output = proportional + (self.ki * self.integral) + (self.kd * derivative)
        self.get_logger().info(f'\n Kp: {proportional} Ki: {self.ki * self.integral} Kd: {self.kd *derivative}')
        
        output = max(min(output, self.max_output), self.min_output)

        self.previous_error = error
        return output

    def depth_callback(self, msg):
        self.depth = msg.relative
        self.timestamp = msg.header.stamp.sec + 1e-09*msg.header.stamp.nanosec
        if self.desired_depth != None:
            self.calc_publish_vertical()
        self.prev_time = self.timestamp
        #self.get_logger().info(f'Depth: {self.depth}, Timestamp: {self.timestamp}')


    def desired_depth_callback(self, msg):
        self.desired_depth = msg.relative
        
    def calc_publish_vertical(self):
        if self.depth is not None:
            depth_correction = self.compute(self.depth - self.desired_depth, self.timestamp - self.prev_time)
            movement = ManualControl()
            movement.z = 50.0 +depth_correction
            self.get_logger().info(f'\nCurrent Power: {depth_correction}/100\nDepth: {self.depth}')
            self.move_publisher.publish(movement)



def main(args=None):
    rclpy.init(args=args)
    move_node = PIDNode()
    try:
        rclpy.spin(move_node)
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt received, shutting down...')
    finally:
        #print(move_node.array)
       #plt.plot(x, move_node.array)
       #plt.savefig("plot.png")
        move_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()




"""
- node:
    pkg: "intro_to_ros"
    exec: "pid"
    name: "pid"
    namespace: ""
"""