import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    whisper_prompt = os.path.join(
        get_package_share_directory("speech_recognition_whisper"),
        "prompt",
        "whisper_prompt.yaml"
        )

    return LaunchDescription(
        [
            Node(
                package="speech_recognition_whisper",
                executable="whisper_server",
                name="whisper_server",
                output="screen",
                parameters=[
                    {
                        "model": "small",
                        "launguage": "en",
                        "task": "transcribe",
                        "sample_rate": 44100,
                        "chunk_size": 16000,
                        "channels": 1,
                        "use_feedback": False,
                        "use_prompt": False,
                    },
                    whisper_prompt,
                ],
            ),
        ]
    )