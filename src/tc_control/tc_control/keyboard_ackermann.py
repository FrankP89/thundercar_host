#!/usr/bin/env python3
"""Simple keyboard Ackermann teleop for simulation (no joystick required)."""

import sys
import termios
import tty

import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from rclpy.node import Node


HELP = """
Keyboard Ackermann teleop
-------------------------
  w / ↑     : forward (always)
  s / ↓     : backward (always)
  a / ←     : steer left
  d / →     : steer right
  x         : center steering
  space     : stop (speed + steer)
  q         : quit
"""


class KeyboardAckermann(Node):
    def __init__(self):
        super().__init__('keyboard_ackermann')
        self.declare_parameter('topic', '/ackermann_cmd')
        self.declare_parameter('speed_step', 0.2)
        self.declare_parameter('steer_step', 0.05)
        self.declare_parameter('max_speed', 1.5)
        self.declare_parameter('max_steer', 0.5)

        topic = self.get_parameter('topic').value
        self.speed_step = float(self.get_parameter('speed_step').value)
        self.steer_step = float(self.get_parameter('steer_step').value)
        self.max_speed = float(self.get_parameter('max_speed').value)
        self.max_steer = float(self.get_parameter('max_steer').value)

        self.speed = 0.0
        self.steer = 0.0
        self.pub = self.create_publisher(AckermannDriveStamped, topic, 10)
        self.timer = self.create_timer(0.05, self._publish)
        self.get_logger().info(HELP)

    def _publish(self):
        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.drive.speed = self.speed
        msg.drive.steering_angle = self.steer
        self.pub.publish(msg)

    def apply_key(self, key: str) -> bool:
        if key in ('q', '\x03'):
            return False

        if key in ('w', 'up'):
            # Always forward: if stopped/reversing, start forward; else speed up
            if self.speed <= 0.0:
                self.speed = self.speed_step
            else:
                self.speed = min(self.max_speed, self.speed + self.speed_step)
        elif key in ('s', 'down'):
            # Always backward
            if self.speed >= 0.0:
                self.speed = -self.speed_step
            else:
                self.speed = max(-self.max_speed, self.speed - self.speed_step)
        elif key in ('a', 'left'):
            self.steer = min(self.max_steer, self.steer + self.steer_step)
        elif key in ('d', 'right'):
            self.steer = max(-self.max_steer, self.steer - self.steer_step)
        elif key == 'x':
            self.steer = 0.0
        elif key == ' ':
            self.speed = 0.0
            self.steer = 0.0
        return True


def _get_key():
    """Read one key; map arrow escape sequences to up/down/left/right."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            # Arrow keys: ESC [ A/B/C/D
            nxt = sys.stdin.read(1)
            if nxt == '[':
                arrow = sys.stdin.read(1)
                return {
                    'A': 'up',
                    'B': 'down',
                    'C': 'right',
                    'D': 'left',
                }.get(arrow, '')
            return ''
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardAckermann()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.0)
            key = _get_key()
            if not key:
                continue
            if not node.apply_key(key):
                break
    except KeyboardInterrupt:
        pass
    finally:
        node.speed = 0.0
        node.steer = 0.0
        node._publish()
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
