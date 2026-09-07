#!/usr/bin/env bash
# Kill leftover Gazebo / RViz / bridge processes from a previous sim.
# Run this before relaunching if the GUI flickers or TF stamps go backwards.
set -euo pipefail

patterns=(
  'gz sim'
  'ros2 launch tc_gazebo'
  'rviz2'
  'parameter_bridge'
  'odom_to_tf'
  'ackermann_to_twist'
  'keyboard_ackermann'
  'joint_state_publisher'
  'robot_state_publisher'
  'point_cloud_xyz'
  'depth_to_points'
)

echo "Stopping leftover Thundercar sim processes..."
for pat in "${patterns[@]}"; do
  pkill -f "$pat" 2>/dev/null || true
done
sleep 0.5

left="$(pgrep -af 'gz sim|rviz2|parameter_bridge|odom_to_tf' || true)"
if [[ -n "${left}" ]]; then
  echo "Still running (try again or kill manually):"
  echo "${left}"
  exit 1
fi

echo "Clean. Relaunch with one GPU window, e.g.:"
echo "  ros2 launch tc_gazebo sim_lvl16.launch.py          # Gazebo GUI only"
echo "  ros2 launch tc_gazebo sim_lvl16.launch.py headless:=true rviz:=true  # RViz only"
