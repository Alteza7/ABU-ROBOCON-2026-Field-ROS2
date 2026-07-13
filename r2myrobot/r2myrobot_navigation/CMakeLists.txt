cmake_minimum_required(VERSION 3.8)
project(r2myrobot_navigation)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch rviz config maps
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
