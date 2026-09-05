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
ros2 launch tc_gazebo sim.launch.py
```

Useful args:

```bash
ros2 launch tc_gazebo sim.launch.py rviz:=true teleop:=true
ros2 launch tc_gazebo sim.launch.py use_joystick:=true   # optional gamepad
ros2 launch tc_gazebo sim.launch.py teleop:=false        # no teleop at all
```

### Drive

- **Keyboard** (default when `teleop:=true`): a new terminal opens with WASD control.
  - `w` / `s` — speed, `a` / `d` — steering, `space` — stop, `q` — quit
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
| Odometry | `/odom`, TF `odom` → `base_link` |
| Drive cmd | `/ackermann_cmd` (`ackermann_msgs/AckermannDriveStamped`) |
| Camera mount | `camera_link` (~0.145, 0, 0.203 m in `base_link`) |

Sim uses Gazebo ground-truth odometry instead of `rf2o` / VESC. Sensors and
actuators are emulated — no Orbbec, SICK, or VESC drivers in this workspace.

## SLAM / localization (goal B)

With the sim running, install/run slam on the host (Jazzy packages), or source a
**read-only** copy of nav tooling. Do not edit `thundercar_ws/software`.

```bash
# Terminal 1 — sim
source /opt/ros/jazzy/setup.bash
source ~/Documents/Personal\ Projects/Thundercar/thundercar_host/install/setup.bash
ros2 launch tc_gazebo sim.launch.py

# Terminal 2 — SLAM (example with apt packages)
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

Or, if you have built `software/core_ros2` somewhere compatible, source it and run
`ros2 launch tc_nav slam.launch.py rviz:=true` (that stack is Humble — prefer
Jazzy slam_toolbox on this 24.04 host).

Save a map:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/sim_indoor
```

The included world `tc_indoor.sdf` is a 10×8 m room with partitions and boxes so
laser SLAM has structure.

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
