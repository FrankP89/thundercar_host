import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Get package share directory
    tc_description_share_dir = get_package_share_directory('tc_description')

    # Define launch arguments
    model_arg = DeclareLaunchArgument(
        'model',
        default_value=os.path.join(tc_description_share_dir, 'urdf', 'tc_viz.xacro')
    )
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='false'
    )

    # Define nodes
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher'
    )
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher'
    )

    # Define launch description
    launch_description = LaunchDescription()
    launch_description.add_action(model_arg)
    launch_description.add_action(gui_arg)
    launch_description.add_action(joint_state_publisher_node)
    launch_description.add_action(robot_state_publisher_node)

    return launch_description
