#!/usr/bin/env bash
# Localize + Nav2 navigate-to-pose against a running Thundercar Gazebo sim.
#
# Terminal 1 — sim WITHOUT teleop / ackermann zeros (Nav2 owns /cmd_vel):
#   ros2 launch tc_gazebo sim_lvl16.launch.py for_nav:=true
#   # or:  ros2 launch tc_gazebo sim_indoor.launch.py for_nav:=true
#
# Terminal 2:
#   ros2 launch tc_gazebo nav_lvl16.launch.py
#   # or:  ros2 launch tc_gazebo nav_indoor.launch.py
#   # or:  ./scripts/navigate_sim.sh maps/lvl16.yaml
#
# In RViz:
#   1) Fixed Frame = map
#   2) 2D Pose Estimate — place the robot on the map
#   3) Nav2 Goal tool — click where to drive

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAP_YAML="${1:-${ROOT}/maps/my_indoor.yaml}"

set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
# shellcheck disable=SC1091
source "${ROOT}/install/setup.bash"
set -u

if [[ ! -f "${MAP_YAML}" ]]; then
  echo "Map not found: ${MAP_YAML}"
  echo "Save one with:  ./scripts/save_map.sh my_indoor"
  exit 1
fi

need=(
  nav2_amcl
  nav2_map_server
  nav2_lifecycle_manager
  nav2_controller
  nav2_planner
  nav2_bt_navigator
  nav2_behaviors
  nav2_velocity_smoother
  nav2_regulated_pure_pursuit_controller
  nav2_navfn_planner
  nav2_smoother
  nav2_waypoint_follower
  nav2_common
)
missing=()
for pkg in "${need[@]}"; do
  if ! ros2 pkg prefix "${pkg}" >/dev/null 2>&1; then
    missing+=("${pkg}")
  fi
done
if ((${#missing[@]})); then
  echo "Missing packages: ${missing[*]}"
  echo "Install with:"
  echo "  sudo apt install ros-jazzy-navigation2"
  exit 1
fi

if ros2 node list 2>/dev/null | grep -q '/slam_toolbox'; then
  echo "WARNING: /slam_toolbox is still running. Stop mapping first."
fi
if ros2 node list 2>/dev/null | grep -q '/ackermann_to_twist'; then
  echo "WARNING: /ackermann_to_twist is running — it will fight Nav2 /cmd_vel."
  echo "Restart sim with:  teleop:=false ackermann_bridge:=false"
fi

echo "Nav2 bringup with map: ${MAP_YAML}"
echo "RViz opens once from launch (~2s). Use 2D Pose Estimate, then Nav2 Goal."
exec ros2 launch tc_gazebo nav_bringup.launch.py \
  "map:=${MAP_YAML}" \
  use_sim_time:=true
