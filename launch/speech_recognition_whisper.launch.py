import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory("speech_recognition_whisper")

    return LaunchDescription([
        DeclareLaunchArgument("stt_name", default_value="whisper"),
        DeclareLaunchArgument("model_name", default_value="small"),
        DeclareLaunchArgument("language", default_value="en"), 
        DeclareLaunchArgument("task", default_value="transcribe"),
        DeclareLaunchArgument("use_prompt", default_value="False"),
        DeclareLaunchArgument("backend", default_value="whisper"),
        DeclareLaunchArgument("device", default_value=""),
        DeclareLaunchArgument("compute_type", default_value="float16"),
        DeclareLaunchArgument("mic_volume", default_value=""),
        DeclareLaunchArgument("use_feedback", default_value="True"),
        
        DeclareLaunchArgument("vad_name", default_value="ten_vad"),
        DeclareLaunchArgument("hop_size", default_value="256"),
        DeclareLaunchArgument("threshold", default_value="0.5"),
        DeclareLaunchArgument("min_wipe_duration", default_value="0.2"),
        DeclareLaunchArgument("extra_audio_duration_sec", default_value="0.2"),
        DeclareLaunchArgument("max_speech_duration", default_value="30.0"),
        
        DeclareLaunchArgument("use_echo_cancel", default_value="False"),
        DeclareLaunchArgument("noise_suppression", default_value="False"),
        DeclareLaunchArgument("analog_gain_control", default_value="False"),
        DeclareLaunchArgument("digital_gain_control", default_value="False"),

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