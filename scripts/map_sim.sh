#!/usr/bin/env bash
# Start online SLAM against a running Thundercar Gazebo sim.
#
# Prefer starting sim WITHOUT its RViz (avoids two RViz + TF spam):
#   ros2 launch tc_gazebo sim_lvl16.launch.py rviz:=false
#   # teleop is capped at 0.4 m/s — keep a slow constant pace while mapping
#
# Then:
#   ./scripts/map_sim.sh
#   # or: ros2 launch tc_gazebo map_lvl16.launch.py
# Drive slowly, then:  ./scripts/save_map.sh [name]

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
# shellcheck disable=SC1091
source "${ROOT}/install/setup.bash"
set -u

if ! ros2 pkg prefix slam_toolbox >/dev/null 2>&1; then
  echo "slam_toolbox not found. Install with:"
  echo "  sudo apt install ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server"
  exit 1
fi

RVIZ="${1:-true}"

echo "Starting slam_toolbox (use_sim_time=true, rviz=${RVIZ})"
echo "Tip: run sim with  ros2 launch tc_gazebo sim.launch.py rviz:=false"
echo "In SLAM RViz, Fixed Frame starts as 'odom'; switch to 'map' after /map appears."
echo "Drive, then save with:  ${ROOT}/scripts/save_map.sh"
exec ros2 launch tc_gazebo slam.launch.py "rviz:=${RVIZ}" use_sim_time:=true
