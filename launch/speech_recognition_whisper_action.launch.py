import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='speech_recognition_whisper',
            executable='whisper_action_server',
            name='whisper_action_server',
            output='screen',
            parameters=[
                {'model': 'small.en'},
                {'sample_rate': 44100},
                {'chunk_size': 4096},
                {'channels': 1},
            ]
        ),
    ])
