#!/usr/bin/env bash
# Launch Thundercar in the lvl16 figure-8 world.
# Prefer:  ros2 launch tc_gazebo sim_lvl16.launch.py
#
# Usage:
#   ./scripts/sim_lvl16.sh
#   ./scripts/sim_lvl16.sh for_nav:=true

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
# shellcheck disable=SC1091
source "${ROOT}/install/setup.bash"
set -u

exec ros2 launch tc_gazebo sim_lvl16.launch.py "$@"
