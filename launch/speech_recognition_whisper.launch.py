import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    launch_description = [
        DeclareLaunchArgument(
            "model_name",
            default_value="small",
            description="Model name: tiny, base, small, medium, large, large-v2, large-v3"
        ),
        DeclareLaunchArgument(
            "language",
            default_value="en",
            description="Language code"
        ),
        DeclareLaunchArgument(
            "task",
            default_value="transcribe",
            description="Task: transcribe or translate"
        ),
        DeclareLaunchArgument(
            "use_prompt",
            default_value="False",
            description="Whether to use initial prompt"
        ),
        DeclareLaunchArgument(
            "device",
            default_value="",
            description="Device: cuda or cpu."
        ),
        DeclareLaunchArgument(
            "backend",
            default_value="whisper",
            description="Backend: whisper or faster-whisper"
        ),
        DeclareLaunchArgument(
            "compute_type",
            default_value="float16",
            description="Compute type when using faster-whisper: float16, int8_float16, int8"
        ),
        DeclareLaunchArgument(
            "mic_volume",
            default_value="",
            description="Microphone volume percentage (e.g. 150)"
        ),
        DeclareLaunchArgument(
            "use_feedback",
            default_value="True",
            description="Enable feedback (VAD)"
        ),
        DeclareLaunchArgument(
            "vad_name",
            default_value="ten_vad",
            description="VAD name: ten_vad or None"
        ),
        DeclareLaunchArgument(
            "hop_size",
            default_value="256",
            description="Hop size for VAD: 160 or 256"
        ),
        DeclareLaunchArgument(
            "threshold",
            default_value="0.5",
            description="VAD threshold"
        ),
        DeclareLaunchArgument(
            "min_wipe_duration",
            default_value="0.2",
            description="Minimum duration to wipe buffer"
        ),
        DeclareLaunchArgument(
            "extra_audio_duration_sec",
            default_value="0.2",
            description="Extra audio duration to keep"
        ),
        DeclareLaunchArgument(
            "max_speech_duration",
            default_value="30.0",
            description="Maximum speech duration before forcing feedback"
        ),
        DeclareLaunchArgument(
            "use_echo_cancel",
            default_value="False",
            description="Enable echo cancellation"
        ),
        DeclareLaunchArgument(
            "noise_suppression",
            default_value="False",
            description="Enable noise suppression"
        ),
        DeclareLaunchArgument(
            "analog_gain_control",
            default_value="False",
            description="Enable analog gain control"
        ),
        DeclareLaunchArgument(
            "digital_gain_control",
            default_value="False",
            description="Enable digital gain control"
        ),
    ]

    whisper_prompt = os.path.join(
        get_package_share_directory("speech_recognition_whisper"),
        "prompt", "whisper_prompt.yaml"
    )

    launch_description.append(Node(
            package="speech_recognition_whisper",
            executable="whisper_server",
            name="whisper_server",
            output="screen",
            parameters=[
                whisper_prompt,
                {
                    "model_name": LaunchConfiguration("model_name"),
                    "language": LaunchConfiguration("language"),
                    "task": LaunchConfiguration("task"),
                    "use_prompt": LaunchConfiguration("use_prompt"),
                    "backend": LaunchConfiguration("backend"),
                    "compute_type": LaunchConfiguration("compute_type"),
                    "device": LaunchConfiguration("device"),
                    "mic_volume": LaunchConfiguration("mic_volume"),
                    "use_feedback": LaunchConfiguration("use_feedback"),
                    "vad_name": LaunchConfiguration("vad_name"),
                    "hop_size": LaunchConfiguration("hop_size"),
                    "threshold": LaunchConfiguration("threshold"),
                    "min_wipe_duration": LaunchConfiguration("min_wipe_duration"),
                    "extra_audio_duration_sec": LaunchConfiguration("extra_audio_duration_sec"),
                    "max_speech_duration": LaunchConfiguration("max_speech_duration"),
                    "use_echo_cancel": LaunchConfiguration("use_echo_cancel"),
                    "noise_suppression": LaunchConfiguration("noise_suppression"),
                    "analog_gain_control": LaunchConfiguration("analog_gain_control"),
                    "digital_gain_control": LaunchConfiguration("digital_gain_control"),
                }
            ]
    ))

    return LaunchDescription(launch_description)