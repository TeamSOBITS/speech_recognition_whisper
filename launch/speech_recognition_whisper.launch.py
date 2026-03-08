import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory("speech_recognition_whisper")

    return LaunchDescription([
        DeclareLaunchArgument(
            "stt_name",
            default_value="whisper",
            description="Name of the STT engine to use (e.g., whisper, vosk)"
        ),
        DeclareLaunchArgument(
            "model_name",
            default_value="small",
            description="Model size or path for the STT engine"
        ),
        DeclareLaunchArgument(
            "language",
            default_value="en",
            description="Language code for recognition (e.g., en, ja)"
        ),
        DeclareLaunchArgument(
            "task",
            default_value="transcribe",
            description="Task type: transcribe or translate"
        ),
        DeclareLaunchArgument(
            "use_prompt",
            default_value="False",
            description="Whether to use initial prompt for Whisper"
        ),
        DeclareLaunchArgument(
            "backend",
            default_value="whisper",
            description="Inference backend (whisper, faster-whisper)"
        ),
        DeclareLaunchArgument(
            "device",
            default_value="",
            description="Device to run inference on (cuda, cpu)"
        ),
        DeclareLaunchArgument(
            "compute_type",
            default_value="float16",
            description="Quantization type (float16, int8, float32)"
        ),
        DeclareLaunchArgument(
            "mic_volume",
            default_value="",
            description="Microphone input volume level"
        ),
        DeclareLaunchArgument(
            "use_feedback",
            default_value="True",
            description="Enable or disable intermediate feedback"
        ),
        DeclareLaunchArgument(
            "vad_name",
            default_value="ten_vad",
            description="Name of the VAD processor to use"
        ),
        DeclareLaunchArgument(
            "hop_size",
            default_value="256",
            description="Hop size for VAD processing"
        ),
        DeclareLaunchArgument(
            "threshold",
            default_value="0.5",
            description="VAD confidence threshold"
        ),
        DeclareLaunchArgument(
            "min_wipe_duration",
            default_value="0.2",
            description="Minimum duration to consider speech finished"
        ),
        DeclareLaunchArgument(
            "extra_audio_duration_sec",
            default_value="0.2",
            description="Extra audio to include at the end of segments"
        ),
        DeclareLaunchArgument(
            "max_speech_duration",
            default_value="30.0",
            description="Maximum duration of a single speech segment"
        ),
        DeclareLaunchArgument(
            "use_echo_cancel",
            default_value="False",
            description="Enable acoustic echo cancellation"
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

        Node(
            package="speech_recognition_whisper",
            executable="whisper_server",
            name="whisper_server",
            output="screen",
            parameters=[
                os.path.join(pkg_share, "prompt", "whisper_prompt.yaml"),
                {
                    "stt_name": LaunchConfiguration("stt_name"),
                    "model_name": LaunchConfiguration("model_name"),
                    "language": LaunchConfiguration("language"),
                    "task": LaunchConfiguration("task"),
                    "device": LaunchConfiguration("device"),
                    "backend": LaunchConfiguration("backend"),
                    "compute_type": LaunchConfiguration("compute_type"),
                    "mic_volume": LaunchConfiguration("mic_volume"),
                    "use_feedback": LaunchConfiguration("use_feedback"),
                    "min_wipe_duration": LaunchConfiguration("min_wipe_duration"),
                    "extra_audio_duration_sec": LaunchConfiguration("extra_audio_duration_sec"),
                    "max_speech_duration": LaunchConfiguration("max_speech_duration"),
                    "vad_name": LaunchConfiguration("vad_name"),
                    "hop_size": LaunchConfiguration("hop_size"),
                    "threshold": LaunchConfiguration("threshold"),
                    "use_echo_cancel": LaunchConfiguration("use_echo_cancel"),
                    "noise_suppression": LaunchConfiguration("noise_suppression"),
                    "analog_gain_control": LaunchConfiguration("analog_gain_control"),
                    "digital_gain_control": LaunchConfiguration("digital_gain_control"),
                    "use_prompt": LaunchConfiguration("use_prompt"),
                }
            ]
        )
    ])