# Thundercar Host — Gazebo Harmonic Simulation

ROS 2 workspace that simulates the Thundercar vehicle in **Gazebo Harmonic**
(`ros_gz`) with the same topic/frame interface as the physical robot stack in
`thundercar_ws/software` (do **not** edit that tree from this repo).

The physical robot runs **Humble** (Jetson). This host PC is expected to run
**Ubuntu 24.04 + ROS 2 Jazzy**, which is the official pairing with Gazebo
Harmonic. Topic names match either way so you can develop navigation against sim
here.

## Prerequisites (Ubuntu 24.04)

```bash
# 1) ROS 2 Jazzy — https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install ros-jazzy-desktop python3-colcon-common-extensions python3-rosdep

# 2) Gazebo Harmonic + ros_gz (Jazzy packages target Harmonic)
sudo apt install \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ackermann-msgs \
  ros-jazzy-joy \
  ros-jazzy-joy-teleop \
  ros-jazzy-depth-image-proc \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-rviz2

# Optional: standalone Harmonic CLI tools
sudo apt install gz-harmonic
```

Then in every new terminal:

```bash
source /opt/ros/jazzy/setup.bash
```

> **Do not** use `source /opt/ros/humble/setup.bash` on this machine — Humble is
> not available on Ubuntu 24.04. Use a 22.04 VM/Docker only if you specifically
> need Humble binaries on the host.

## Build

```bash
cd ~/Documents/Personal\ Projects/Thundercar/thundercar_host
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Run simulation

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

**Per-map sim launches** (preferred):

```bash
ros2 launch tc_gazebo sim_lvl16.launch.py      # figure-8 blueprint world
ros2 launch tc_gazebo sim_indoor.launch.py     # small indoor room
```

Generic (any world path):

```bash
ros2 launch tc_gazebo sim.launch.py
```

Useful args (also work on `sim_lvl16` / `sim_indoor`):

```bash
ros2 launch tc_gazebo sim_lvl16.launch.py rviz:=false
ros2 launch tc_gazebo sim_lvl16.launch.py for_nav:=true   # Nav2 owns /cmd_vel
ros2 launch tc_gazebo sim_indoor.launch.py use_joystick:=true
```

### Blueprint world (lvl16 figure-8)

`worlds/tc_lvl16.sdf` — 22.12×12.74 m figure-8 corridor, white walls, tiled floor.
Origin at map center; spawn is the lower-left corridor.

```bash
# Drive / map — keep slow constant speed (teleop capped at 0.4 m/s)
ros2 launch tc_gazebo sim_lvl16.launch.py rviz:=false   # terminal 1
ros2 launch tc_gazebo map_lvl16.launch.py               # terminal 2
./scripts/save_map.sh lvl16

# Faster free driving (not for mapping):
# ros2 launch tc_gazebo sim_lvl16.launch.py max_speed:=1.2

# Navigate
ros2 launch tc_gazebo sim_lvl16.launch.py for_nav:=true  # terminal 1
ros2 launch tc_gazebo nav_lvl16.launch.py                # terminal 2
```

Remap after switching worlds — old maps won’t match.

**Mapping tip:** drive slowly and steadily. High speed or stop/start bursts
make slam_toolbox warp the map (especially in long corridors).

### Drive

- **Keyboard** (default when `teleop:=true`): a new terminal opens with WASD control.
  - `w` / `s` — speed, `a` / `d` — steering, `space` — stop, `q` — quit
  - Default **max speed 0.4 m/s** (mapping-safe); raise with `max_speed:=1.2`
  - Publishes `/ackermann_cmd`
  - If no terminal emulator is found, run manually:

```bash
ros2 run tc_control keyboard_ackermann
```

- **Joystick** (`use_joystick:=true`): hold **Left Bumper** (button 6). Skipped quietly if `joy` / `joy_teleop` are not installed.

## Topic / frame parity (vs physical robot)

| Interface | Topic / frame |
|-----------|----------------|
| Lidar | `/scan`, frame `laser` |
| Color | `/camera/color/image_raw`, `/camera/color/camera_info` |
| Depth | `/camera/depth/image_raw`, `/camera/depth/camera_info` |
| Points | `/camera/depth/points` |
| Odometry | `/odom` (Gazebo ground-truth pose), TF `odom` → `base_link` |
| Wheel odom (diag) | `/odom_wheel` (Ackermann-integrated; not used for TF) |
| Drive cmd | `/ackermann_cmd` (`ackermann_msgs/AckermannDriveStamped`) |
| Camera mount | `camera_link` (~0.145, 0, 0.203 m in `base_link`) |

Sim uses Gazebo **ground-truth** model pose for `/odom` (via `OdometryPublisher`),
not wheel-integrated Ackermann odom — so laser walls stay fixed in RViz when
Fixed Frame is `odom`. Sensors and actuators are emulated — no Orbbec, SICK, or
VESC drivers in this workspace.

### Check odom / laser / TF (walls should stay fixed)

After a full relaunch (`colcon build`, kill leftover `gz sim`, then `sim.launch.py`):

```bash
ros2 topic echo /odom --once          # header.frame_id=odom, child_frame_id=base_link
ros2 topic echo /scan --once          # header.frame_id=laser
ros2 run tf2_tools view_frames        # odom -> base_link -> ... -> laser
```

In RViz set **Fixed Frame** to `odom`. Drive straight at a wall corner — the
corner stays fixed on the grid while the robot approaches it. If walls slide
with the robot, Fixed Frame is likely still `base_link`, or an old sim process
is still publishing wheel odom on `/odom`.

## SLAM / mapping (goal B)

With the sim running in another terminal:

```bash
# Once: SLAM deps
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server

# Build (if you just pulled these files)
colcon build --symlink-install --packages-select tc_gazebo
source install/setup.bash

# Start mapping (prefer sim without its own RViz)
#   ros2 launch tc_gazebo sim_lvl16.launch.py rviz:=false
#   ros2 launch tc_gazebo map_lvl16.launch.py
./scripts/map_sim.sh
# or:  ros2 launch tc_gazebo slam.launch.py
#
# Drive slowly and steadily (teleop max_speed defaults to 0.4 m/s).
# SLAM RViz Fixed Frame is map; switch to odom only if TF warnings appear.

Drive the indoor world with keyboard teleop. When the map looks good:

```bash
./scripts/save_map.sh              # -> maps/sim_indoor_<timestamp>.{pgm,yaml}
./scripts/save_map.sh my_office    # -> maps/my_office.{pgm,yaml}
```

Do not edit `thundercar_ws/software`. Worlds in `tc_gazebo/worlds/`:
`tc_indoor.sdf` (small room) and `tc_lvl16.sdf` (figure-8 blueprint).

## Localization (on a saved map)

Stop mapping first. Keep the sim running (`rviz:=false`).

```bash
# Once: AMCL stack
sudo apt install ros-jazzy-nav2-amcl ros-jazzy-nav2-lifecycle-manager

./scripts/localize_sim.sh
# or:  ./scripts/localize_sim.sh maps/my_indoor.yaml
```

In RViz (Fixed Frame `map`): if the laser does not sit on the walls, use
**2D Pose Estimate** to place the robot on the map, then drive — the particle
cloud should tighten.

## Navigation (Nav2 — drive to a goal)

Stop mapping/localization first. Restart sim so Nav2 owns `/cmd_vel`:

```bash
# Once
sudo apt install ros-jazzy-navigation2

# Terminal 1 — no teleop bridge
ros2 launch tc_gazebo sim_lvl16.launch.py for_nav:=true
# or: ros2 launch tc_gazebo sim_indoor.launch.py for_nav:=true

# Terminal 2
ros2 launch tc_gazebo nav_lvl16.launch.py
# or: ros2 launch tc_gazebo nav_indoor.launch.py
# or: ./scripts/navigate_sim.sh maps/my_indoor.yaml
# or: ./scripts/navigate_sim.sh maps/my_indoor.yaml
```

In RViz: **2D Pose Estimate**, then **2D Goal Pose**. The car should plan a
path and drive there (Regulated Pure Pursuit → Twist → Gazebo Ackermann).

If the car gets jammed in a wall/corner:

```bash
./scripts/unstick.sh          # reverse ~2.5 s
./scripts/unstick.sh 3.0 0.5  # longer / faster reverse
```

Then re-set **2D Pose Estimate** and send a new goal.

## Packages

| Package | Role |
|---------|------|
| `tc_description` | URDF/xacro, meshes, Gazebo Harmonic sensors + Ackermann plugin |
| `tc_gazebo` | Indoor world, `sim.launch.py`, `ros_gz` bridge, RViz |
| `tc_control` | Ackermann→Twist, odom→TF, keyboard/joy teleop |

## Out of scope (v1)

- Edits under `thundercar_ws/software`
- Isaac Sim
- Pixel-perfect Femto Bolt intrinsics
- VESC / Orbbec / sick_scan_xd drivers in sim
