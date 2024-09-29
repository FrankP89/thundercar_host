import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Get package share directories
    #mynt_eye_ros_wrapper_share_dir = get_package_share_directory('mynt_eye_ros_wrapper')
    sick_tim_share_dir = get_package_share_directory('sick_tim')
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

    # Include other launch files
    #mynteye_launch = IncludeLaunchDescription(
    #    PythonLaunchDescriptionSource(os.path.join(mynt_eye_ros_wrapper_share_dir, 'launch', 'mynteye.launch'))
    #)
    sick_tim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(sick_tim_share_dir, 'launch', 'tc_tim571.launch'))
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
    tf_remapper_node = Node(
        package='tf',
        executable='tf_remap',
        name='tf_remapper',
        output='screen',
        parameters=[{'mappings': [{'old': '/myntai_link', 'new': '/mynteye_link'}]}]
    )

    # Define launch description
    launch_description = LaunchDescription()
    launch_description.add_action(model_arg)
    launch_description.add_action(gui_arg)
    #launch_description.add_action(mynteye_launch)
    launch_description.add_action(sick_tim_launch)
    launch_description.add_action(joint_state_publisher_node)
    launch_description.add_action(robot_state_publisher_node)
    launch_description.add_action(tf_remapper_node)

    return launch_description
