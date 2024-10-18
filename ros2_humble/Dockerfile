FROM osrf/ros:humble-desktop

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# set environment variables
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ENV ROS_DISTRO humble
RUN apt-get update -y 

# install ros package
RUN apt-get install -y \
      ros-${ROS_DISTRO}-demo-nodes-cpp \
      ros-${ROS_DISTRO}-demo-nodes-py && \
    rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/$ROS_DISTRO/local_setup.bash" >> ~/.bashrc

RUN source ~/.bashrc

# launch ros package
CMD ["ros2", "launch", "demo_nodes_cpp", "talker_listener.launch.py"]
