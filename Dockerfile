FROM ros:melodic

# install ros package
RUN apt-get update && apt-get install -y \
      ros-${ROS_DISTRO}-ros-tutorials \
      ros-${ROS_DISTRO}-common-tutorials && \
    rm -rf /var/lib/apt/lists/*

# launch ros package - demo
# CMD ["roslaunch", "roscpp_tutorials", "talker_listener_launch"]
