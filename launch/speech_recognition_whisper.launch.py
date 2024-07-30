import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='speech_recognition_whisper',
            executable='whisper_server',
            name='whisper_server',
            output='screen',
            parameters=[
                {'model': 'small.en'},
                {'sample_rate': 16000},
                {'chunk_size': 1024},
                {'channels': 1},
            ]
        ),
    ])
