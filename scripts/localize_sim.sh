#!/usr/bin/env bash
# Localize on a saved map against a running Thundercar Gazebo sim.
#
# Stop mapping first (Ctrl+C map_sim.sh). Keep sim running:
#   ros2 launch tc_gazebo sim.launch.py rviz:=false
#
# Then:
#   ./scripts/localize_sim.sh
#   ./scripts/localize_sim.sh maps/my_indoor.yaml
#
# In RViz: Fixed Frame = map. Use "2D Pose Estimate" to set the robot on the
# map if the laser does not line up with the walls.

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

for pkg in nav2_amcl nav2_map_server nav2_lifecycle_manager; do
  if ! ros2 pkg prefix "${pkg}" >/dev/null 2>&1; then
    echo "Missing ${pkg}. Install with:"
    echo "  sudo apt install ros-jazzy-navigation2"
    echo "  # or: sudo apt install ros-jazzy-nav2-amcl ros-jazzy-nav2-map-server ros-jazzy-nav2-lifecycle-manager"
    exit 1
  fi
done

# Mapping and localization both want /map — warn if slam is still up
if ros2 node list 2>/dev/null | grep -q '/slam_toolbox'; then
  echo "WARNING: /slam_toolbox is still running. Stop map_sim.sh first (Ctrl+C)."
fi

echo "Localizing with map: ${MAP_YAML}"
echo "In RViz use '2D Pose Estimate' if the scan does not align with the map."
exec ros2 launch tc_gazebo localization.launch.py \
  "map:=${MAP_YAML}" \
  use_sim_time:=true \
  rviz:=true
