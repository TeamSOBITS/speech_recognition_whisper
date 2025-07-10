import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_feedback_arg = DeclareLaunchArgument(
        "use_feedback",
        default_value="False",
        description="Enable feedback (WIP Transcriber)"
    )
    use_feedback = LaunchConfiguration("use_feedback")

    shared_params = {
        "model_name": "small",
        "language": "en",
        "task": "transcribe",
        "use_feedback": use_feedback,
        "use_prompt": False,
        "replace_prompt_whisper": [""],
    }

    wip_transcriber_node = Node(
        package="speech_recognition_whisper",
        executable="wip_transcriber",
        name="wip_transcriber",
        output="screen",
        condition=IfCondition(use_feedback),
        parameters=[
            shared_params,
        ],
    )

    whisper_prompt = os.path.join(
        get_package_share_directory("speech_recognition_whisper"),
        "prompt",
        "whisper_prompt.yaml"
    )

    whisper_server_node = Node(
        package="speech_recognition_whisper",
        executable="whisper_server",
        name="whisper_server",
        output="screen",
        parameters=[
            whisper_prompt,
            shared_params,
        ],
    )

    return LaunchDescription([
        use_feedback_arg,
        whisper_server_node,
        wip_transcriber_node,
    ])