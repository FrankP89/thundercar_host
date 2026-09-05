cmake_minimum_required(VERSION 3.8)
project(tc_gazebo)

find_package(ament_cmake REQUIRED)

install(DIRECTORY worlds launch config rviz behavior_trees
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
