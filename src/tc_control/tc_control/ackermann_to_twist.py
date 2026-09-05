#!/usr/bin/env python3
"""Convert AckermannDriveStamped to Twist for Gazebo AckermannSteering.

Publishes zeros when commands go stale so the car does not keep the last
non-zero cmd_vel (common cause of 'drifts with no input').
"""

import math

import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.time import Time


class AckermannToTwist(Node):
    def __init__(self):
        super().__init__('ackermann_to_twist')
        self.declare_parameter('ackermann_topic', '/ackermann_cmd')
        self.declare_parameter('twist_topic', '/cmd_vel')
        self.declare_parameter('wheelbase', 0.34)
        # Stop commanding motion if no Ackermann msg for this long [s]
        self.declare_parameter('cmd_timeout', 0.25)

        ack_topic = self.get_parameter('ackermann_topic').value
        twist_topic = self.get_parameter('twist_topic').value
        self.wheelbase = float(self.get_parameter('wheelbase').value)
        self.cmd_timeout = float(self.get_parameter('cmd_timeout').value)

        self._last_cmd_time: Time | None = None
        self._last_twist = Twist()

        self.pub = self.create_publisher(Twist, twist_topic, 10)
        self.sub = self.create_subscription(
            AckermannDriveStamped, ack_topic, self._cb, 10
        )
        # 20 Hz: keep sending zeros (or last cmd) so gz never holds a stale twist
        self.create_timer(0.05, self._timer_cb)
        self.get_logger().info(
            f'Bridging {ack_topic} -> {twist_topic} '
            f'(wheelbase={self.wheelbase}, timeout={self.cmd_timeout}s)'
        )

    def _cb(self, msg: AckermannDriveStamped):
        speed = float(msg.drive.speed)
        steering = float(msg.drive.steering_angle)

        twist = Twist()
        twist.linear.x = speed
        if abs(self.wheelbase) > 1e-6 and abs(speed) > 1e-6:
            twist.angular.z = speed * math.tan(steering) / self.wheelbase
        else:
            # No forward speed => no yaw command (avoids spinning in place from steer bias)
            twist.angular.z = 0.0

        self._last_twist = twist
        self._last_cmd_time = self.get_clock().now()
        self.pub.publish(twist)

    def _timer_cb(self):
        now = self.get_clock().now()
        if self._last_cmd_time is None:
            self.pub.publish(Twist())
            return
        age = (now - self._last_cmd_time).nanoseconds / 1e9
        if age > self.cmd_timeout:
            self.pub.publish(Twist())
        else:
            self.pub.publish(self._last_twist)


def main(args=None):
    rclpy.init(args=args)
    node = AckermannToTwist()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
