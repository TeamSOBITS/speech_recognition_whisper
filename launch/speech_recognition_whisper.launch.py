import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

extra_params = {
    "backend": "whisper",    # "whisper" or "faster-whisper"
    "model_name": "small",   # tiny, base, small, medium, large, large-v2, large-v3, large-v3-turbo
    "language": "en",
    "task": "transcribe",
    "use_prompt": False,
    "use_feedback": True,
    "vad_name": "ten_vad",
    "hop_size": 256,
    "threshold": 0.5,
    "min_wipe_duration": 0.2,
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
