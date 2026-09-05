#!/usr/bin/env python3
"""Republish odom -> base_link TF from nav_msgs/Odometry (sim ground truth).

Uses the odometry header stamp so LaserScan / other sensors (also sim-stamped)
transform correctly. Using clock-now here makes walls 'slide' with the robot in
RViz (scan at time T drawn with TF at time T+dt).
"""

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class OdomToTf(Node):
    def __init__(self):
        super().__init__('odom_to_tf')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        topic = self.get_parameter('odom_topic').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value

        self._last_stamp_ns = None
        self.br = TransformBroadcaster(self)
        self.sub = self.create_subscription(Odometry, topic, self._cb, 50)
        self.get_logger().info(
            f'Broadcasting TF {self.odom_frame} -> {self.base_frame} from {topic}'
        )

    def _cb(self, msg: Odometry):
        stamp = msg.header.stamp
        stamp_ns = stamp.sec * 10**9 + stamp.nanosec
        # Skip backwards jumps after Gazebo restart (avoids TF_OLD_DATA spam)
        if self._last_stamp_ns is not None and stamp_ns < self._last_stamp_ns:
            self.get_logger().warn(
                'odom stamp went backwards — resetting TF timeline',
                throttle_duration_sec=2.0,
            )
            self._last_stamp_ns = None
            return
        self._last_stamp_ns = stamp_ns

        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self.br.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
