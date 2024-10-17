FROM ros:noetic

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# set environment variables
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ENV ROS_DISTRO noetic

# install ros package
RUN apt-get update && apt-get install -y \
      ros-${ROS_DISTRO}-ros-tutorials \
      ros-${ROS_DISTRO}-common-tutorials && \
    rm -rf /var/lib/apt/lists/*


RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
# RUN source /opt/ros/${ROS_DISTRO}/setup.bash
RUN source ~/.bashrc


RUN sh ros_entrypoint.sh
# RUN roscore

# launch ros package
CMD ["roslaunch", "roscpp_tutorials", "talker_listener.launch"]
# CMD ["ls", "-la"]
# CMD ["roscore"]