import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'speech_recognition_whisper'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, "launch"), glob('launch/*')),
        (os.path.join('share', package_name, "sound_file"), glob('sound_file/*')),
        (os.path.join('share', package_name, "prompt"), glob('prompt/*')),
        
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sobits',
    maintainer_email='sobits@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            "whisper_server = speech_recognition_whisper.whisper_server:main",
        ],
    },
)