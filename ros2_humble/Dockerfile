FROM ros:humble

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# set environment variables
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8


ENV ROS_DISTRO humble

# install ros package
RUN apt-get update && apt-get install -y \
      ros-${ROS_DISTRO}-demo-nodes-cpp \
      ros-${ROS_DISTRO}-demo-nodes-py && \
    rm -rf /var/lib/apt/lists/*


RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc

RUN source ~/.bashrc


RUN sh ros_entrypoint.sh
# RUN roscore


# launch ros package
CMD ["ros2", "launch", "demo_nodes_cpp", "talker_listener_launch.py"]
