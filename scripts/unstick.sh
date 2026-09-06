#!/usr/bin/env bash
# Reverse the sim car briefly to get off a wall / corner.
#
# Usage:
#   ./scripts/unstick.sh           # reverse 0.4 m/s for 2.5 s
#   ./scripts/unstick.sh 3.0       # duration [s]
#   ./scripts/unstick.sh 3.0 0.5   # duration [s], speed [m/s] (negative applied)
#
# Cancels an active navigate_to_pose goal first (best-effort), then publishes
# /cmd_vel reverse, then zeros. Re-set 2D Pose Estimate in RViz afterward.

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DURATION="${1:-2.5}"
SPEED="${2:-0.4}"

set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
# shellcheck disable=SC1091
source "${ROOT}/install/setup.bash"
set -u

# Always reverse
if awk "BEGIN {exit !($SPEED > 0)}"; then
  SPEED="$(awk "BEGIN {print -($SPEED)}")"
fi

echo "Unstick: cancel nav (best-effort), reverse ${SPEED} m/s for ${DURATION}s on /cmd_vel"

# Cancel all NavigateToPose goals (zero UUID = cancel all on that server)
ros2 service call /navigate_to_pose/_action/cancel_goal action_msgs/srv/CancelGoal \
  "{}" >/dev/null 2>&1 || true
sleep 0.3

# Zero any residual command first
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" >/dev/null

END_TS="$(awk "BEGIN {print systime() + ${DURATION}}")"
while awk "BEGIN {exit !(systime() < ${END_TS})}"; do
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: ${SPEED}, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" >/dev/null
  sleep 0.1
done

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" >/dev/null

echo "Done. In RViz: Cancel if still navigating → 2D Pose Estimate → new goal."
