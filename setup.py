import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'speech_recognition_whisper'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (os.path.join('share', package_name), glob('launch/speech_recognition_whisper.launch.py')),
    ],
    install_requires=['setuptools', 'whisper',
        'pyaudio',
        'playsound',],
    zip_safe=True,
    maintainer='sobits',
    maintainer_email='sobits@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "whisper_server = speech_recognition_whisper.whisper_server:main",
        ],
    },
)