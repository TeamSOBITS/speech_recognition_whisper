import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

extra_params = {
    "model_name": "small",   # tiny, base, small, medium, large, large-v2, large-v3
    "language": "en",        
    "task": "transcribe",    # "transcribe" or "translate" 
    "use_prompt": False,
    "backend": "whisper",    # "whisper" or "faster-whisper"
    "compute_type": "float16", # "float16", "int8_float16", "int8"
    "mic_volume": "", 
    "use_feedback": True,
    "vad_name": "ten_vad",    # "ten_vad" or "None"
    "hop_size": 256,         # 160 or 256
    "threshold": 0.5,        
    "min_wipe_duration": 0.2,
    "extra_audio_duration_sec": 0.2,
    "use_echo_cancel": False,
    "noise_suppression": False,
    "analog_gain_control": False,
    "digital_gain_control": False,
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