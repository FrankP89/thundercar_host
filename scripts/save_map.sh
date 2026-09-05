#!/usr/bin/env bash
# Save the current slam_toolbox /map to maps/<name>.{pgm,yaml}
#
# Usage:  ./scripts/save_map.sh [name]
# Default name: sim_indoor_<timestamp>
#
# Requires slam_toolbox to be active and publishing /map
# (ros2 topic info /map  →  Publisher count: 1).

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPS_DIR="${ROOT}/maps"
NAME="${1:-sim_indoor_$(date +%Y%m%d_%H%M%S)}"
OUT="${MAPS_DIR}/${NAME}"

set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
# shellcheck disable=SC1091
source "${ROOT}/install/setup.bash"
set -u

if ! ros2 pkg prefix nav2_map_server >/dev/null 2>&1; then
  echo "nav2_map_server not found. Install with:"
  echo "  sudo apt install ros-jazzy-nav2-map-server"
  exit 1
fi

# Fail fast if /map has no publisher (slam not active / no map yet)
PUBS="$(ros2 topic info /map 2>/dev/null | awk '/Publisher count:/{print $3; exit}')"
if [[ -z "${PUBS}" || "${PUBS}" -lt 1 ]]; then
  echo "ERROR: nothing is publishing /map (Publisher count: ${PUBS:-0})."
  echo "Is slam running and activated? Check:"
  echo "  ros2 lifecycle get /slam_toolbox    # should be 'active'"
  echo "  ros2 topic echo /map --once"
  echo "Restart mapping with:  ./scripts/map_sim.sh"
  exit 1
fi

mkdir -p "${MAPS_DIR}"
echo "Saving /map -> ${OUT}.{pgm,yaml}  (use_sim_time=true, timeout=15s)"
ros2 run nav2_map_server map_saver_cli -f "${OUT}" --ros-args \
  -p use_sim_time:=true \
  -p save_map_timeout:=15.0
echo "Done: ${OUT}.yaml"
