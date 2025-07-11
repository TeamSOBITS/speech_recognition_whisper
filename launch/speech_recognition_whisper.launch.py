import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

extra_params = {
    "model_name": "small",
    "language": "en",
    "task": "transcribe",
    "use_prompt": False,
    "replace_prompt_whisper": [""],
    "use_feedback": False,
}

whisper_prompt = os.path.join(
    get_package_share_directory("speech_recognition_whisper"),
    "prompt", "whisper_prompt.yaml"
)

whisper_server_node = Node(
    package="speech_recognition_whisper",
    executable="whisper_server",
    name="whisper_server",
    output="screen",
    parameters=[whisper_prompt, extra_params]
)

def generate_launch_description():
    return LaunchDescription([whisper_server_node])