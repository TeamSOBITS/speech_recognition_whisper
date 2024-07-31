make_minimum_required(VERSION 3.8)
project(speech_recognition_whisper)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sobits_msgs REQUIRED)
find_package(ament_index_python REQUIRED)

# Install directories
install(DIRECTORY mp3/
  DESTINATION share/${PROJECT_NAME}/mp3
)

install(DIRECTORY sound_file/
  DESTINATION share/${PROJECT_NAME}/sound_file
)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install scripts
install(PROGRAMS
  speech_recognition_whisper/whisper_server.py
  DESTINATION lib/${PROJECT_NAME}
)

# Package
ament_package()