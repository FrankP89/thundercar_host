#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Define arguments
    
    model_arg = DeclareLaunchArgument(
        'model',
        default_value=os.path.join(get_package_share_directory('tc_description'), 'urdf', 'tc_viz.xacro')
    )
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true'
    )
    rvizconfig_arg = DeclareLaunchArgument(
        'rvizconfig',
        default_value=os.path.join(get_package_share_directory('tc_description'), 'rviz', 'rviz_tc.rviz')
    )

    # Define nodes
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher'
    )
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher'
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
        required=True
    )

    # Define parameters
    robot_description_param = {'robot_description': os.path.join(get_package_share_directory('xacro'), 'xacro', '--inorder', model_arg)}
    gui_param = {'gui': gui_arg}

    # Create launch description
    ld = LaunchDescription()
    ld.add_action(model_arg)
    ld.add_action(gui_arg)
    ld.add_action(rvizconfig_arg)
    ld.add_action(joint_state_publisher_node)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(rviz_node)
    ld.add_action(robot_description_param)
    ld.add_action(gui_param)

    return ld
