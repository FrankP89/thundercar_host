"""Thundercar Gazebo Harmonic bringup.

Starts gz sim, spawns the robot, bridges sensor/cmd topics to ROS 2 names that
match the physical stack (/scan, /camera/..., /odom, /ackermann_cmd), and
optionally launches teleop + RViz.
"""

import os
import shlex
import subprocess

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _setup(context, *args, **kwargs):
    """Build the launch graph after launch args are resolved (needs context)."""
    tc_desc = get_package_share_directory('tc_description')
    tc_gazebo = get_package_share_directory('tc_gazebo')

    # LaunchConfiguration handles (booleans stay as substitutions for IfCondition)
    use_sim_time = LaunchConfiguration('use_sim_time')
    world = LaunchConfiguration('world').perform(context)
    x = LaunchConfiguration('x').perform(context)
    y = LaunchConfiguration('y').perform(context)
    z = LaunchConfiguration('z').perform(context)
    yaw = LaunchConfiguration('yaw').perform(context)
    rviz = LaunchConfiguration('rviz')
    teleop = LaunchConfiguration('teleop')

    urdf_file = os.path.join(tc_desc, 'urdf', 'tc.urdf.xacro')
    rviz_config = os.path.join(tc_gazebo, 'rviz', 'sim.rviz')

    # Expand xacro once so both RSP and gz spawn get the same URDF+plugin XML
    robot_xml = subprocess.check_output(['xacro', urdf_file], text=True)

    # --- Mesh / world discovery for Gazebo ---------------------------------
    # Gazebo resolves package:// via share roots on GZ_SIM_RESOURCE_PATH.
    # Keep IGN_* alias for older ros_gz helpers.
    share_roots = []
    for prefix in os.environ.get('AMENT_PREFIX_PATH', '').split(os.pathsep):
        share = os.path.join(prefix, 'share')
        if os.path.isdir(share):
            share_roots.append(share)
    resource_paths = share_roots + [
        os.path.join(tc_desc, 'meshes'),
        os.path.join(tc_gazebo, 'worlds'),
    ]
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    if existing:
        resource_paths.append(existing)
    gz_path = os.pathsep.join(resource_paths)

    set_gz_path = SetEnvironmentVariable(name='GZ_SIM_RESOURCE_PATH', value=gz_path)
    set_ign_path = SetEnvironmentVariable(name='IGN_GAZEBO_RESOURCE_PATH', value=gz_path)

    # --- Gazebo Harmonic ---------------------------------------------------
    # -r = run immediately, -v 1 = modest console verbosity
    # Quote the world path: workspace lives under "Personal Projects" (space).
    # ros_gz_sim runs `gz sim` with shell=True; unquoted paths break at the space
    # ("Unable to find or download file") so Gazebo never starts — RViz then shows
    # a white robot with everything stuck at the origin.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])
        ),
        launch_arguments={
            'gz_args': f'-r -v 1 {shlex.quote(world)}',
        }.items(),
    )

    # Publishes TF for fixed/joint frames from robot_description
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_xml,
            'use_sim_time': True,
        }],
    )

    # Prefer joint_state_publisher; otherwise bridge gz joints directly to /joint_states
    actions_after_rsp = []
    has_jsp = False
    try:
        get_package_share_directory('joint_state_publisher')
        has_jsp = True
    except PackageNotFoundError:
        has_jsp = False

    if has_jsp:
        bridge_config = os.path.join(tc_gazebo, 'config', 'ros_gz_bridge.yaml')
        actions_after_rsp.append(
            Node(
                package='joint_state_publisher',
                executable='joint_state_publisher',
                name='joint_state_publisher',
                output='screen',
                parameters=[{
                    'robot_description': robot_xml,
                    'use_sim_time': True,
                    'source_list': ['gz_joint_states'],
                    'rate': 50.0,
                }],
            )
        )
    else:
        bridge_config = os.path.join(tc_gazebo, 'config', 'ros_gz_bridge_no_jsp.yaml')
        actions_after_rsp.append(
            LogInfo(
                msg='joint_state_publisher not installed — bridging gz joints to '
                '/joint_states directly. Optional improve RViz wheels with:\n'
                '  sudo apt install ros-jazzy-joint-state-publisher'
            )
        )

    # Delay spawn until the world is up. Remove any existing "thundercar" first —
    # a leftover model (old camera orientation) would keep publishing on the same
    # image topics and make the camera blink between side/front views.
    create = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'thundercar',
            '-string', robot_xml,
            '-x', x,
            '-y', y,
            '-z', z,
            '-Y', yaw,
        ],
        parameters=[{'use_sim_time': True}],
    )
    remove_then_spawn = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'bash', '-c',
                    'gz service -s /world/tc_indoor/remove '
                    '--reqtype gz.msgs.Entity --reptype gz.msgs.Boolean '
                    '--timeout 1000 --req \'name: "thundercar", type: MODEL\' '
                    '>/dev/null 2>&1 || true',
                ],
                output='screen',
            ),
            TimerAction(period=1.0, actions=[create]),
        ],
    )

    # --- Bridges / adapters (Gazebo <-> ROS topic parity) ------------------
    # Maps /scan, cameras, /odom, /cmd_vel, /joint_states, /clock
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True,
        }],
    )

    # Ground-truth /odom from AckermannSteering does not publish ROS TF;
    # broadcast odom -> base_link so slam_toolbox / AMCL can use the same tree
    odom_tf = Node(
        package='tc_control',
        executable='odom_to_tf',
        name='odom_to_tf',
        output='screen',
        parameters=[{
            'odom_topic': '/odom',
            'odom_frame': 'odom',
            'base_frame': 'base_link',
            'use_sim_time': True,
        }],
    )

    # Physical teleop uses AckermannDriveStamped; gz AckermannSteering wants Twist
    ack_to_twist = Node(
        package='tc_control',
        executable='ackermann_to_twist',
        name='ackermann_to_twist',
        output='screen',
        parameters=[{
            'ackermann_topic': '/ackermann_cmd',
            'twist_topic': '/cmd_vel',
            'wheelbase': 0.34,
            'use_sim_time': True,
        }],
    )

    # Match robot topic /camera/depth/points (Orbbec publishes this natively)
    depth_cloud = Node(
        package='depth_image_proc',
        executable='point_cloud_xyz_node',
        name='depth_to_points',
        output='screen',
        remappings=[
            ('image_rect', '/camera/depth/image_raw'),
            ('camera_info', '/camera/depth/camera_info'),
            ('points', '/camera/depth/points'),
        ],
        parameters=[{'use_sim_time': True}],
    )

    # Teleop -> /ackermann_cmd (keyboard by default; joystick optional)
    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('tc_control'), 'launch', 'teleop.launch.py'])
        ),
        condition=IfCondition(teleop),
        launch_arguments={
            'use_keyboard': LaunchConfiguration('use_keyboard'),
            'use_joystick': LaunchConfiguration('use_joystick'),
        }.items(),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        condition=IfCondition(rviz),
        parameters=[{'use_sim_time': True}],
    )

    return [
        set_gz_path,
        set_ign_path,
        gz_sim,
        rsp,
        *actions_after_rsp,
        remove_then_spawn,
        bridge,
        odom_tf,
        ack_to_twist,
        depth_cloud,
        teleop_launch,
        rviz_node,
    ]


def generate_launch_description():
    """Declare CLI args, then defer node construction to _setup via OpaqueFunction."""
    tc_gazebo = get_package_share_directory('tc_gazebo')
    default_world = os.path.join(tc_gazebo, 'worlds', 'tc_indoor.sdf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use /clock from Gazebo',
        ),
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Path to SDF world (indoor map by default)',
        ),
        DeclareLaunchArgument('x', default_value='-2.0', description='Spawn x [m]'),
        DeclareLaunchArgument('y', default_value='0.0', description='Spawn y [m]'),
        DeclareLaunchArgument('z', default_value='0.15', description='Spawn z [m]'),
        DeclareLaunchArgument('yaw', default_value='0.0', description='Spawn yaw [rad]'),
        DeclareLaunchArgument('rviz', default_value='true', description='Start RViz2'),
        DeclareLaunchArgument(
            'teleop',
            default_value='true',
            description='Start teleop helpers (keyboard and/or joystick)',
        ),
        DeclareLaunchArgument(
            'use_keyboard',
            default_value='true',
            description='Keyboard Ackermann teleop (w/a/s/d) in a new terminal',
        ),
        DeclareLaunchArgument(
            'use_joystick',
            default_value='false',
            description='Joystick teleop if joy packages are installed; otherwise ignored',
        ),
        # OpaqueFunction so spawn pose / world path are concrete strings
        OpaqueFunction(function=_setup),
    ])
