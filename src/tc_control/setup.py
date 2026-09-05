from setuptools import setup

package_name = 'tc_control'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        (f'share/{package_name}', ['package.xml']),
        (f'share/{package_name}/launch', [
            'launch/teleop.launch.py',
        ]),
        (f'share/{package_name}/config', [
            'config/joy_teleop.yaml',
            'config/joy_node.yaml',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='frank',
    maintainer_email='frank@todo.todo',
    description='Ackermann teleop and odometry helpers for Thundercar Gazebo sim',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'ackermann_to_twist = tc_control.ackermann_to_twist:main',
            'odom_to_tf = tc_control.odom_to_tf:main',
            'keyboard_ackermann = tc_control.keyboard_ackermann:main',
        ],
    },
)
