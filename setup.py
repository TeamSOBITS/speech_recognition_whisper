import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'speech_recognition_whisper'

setup(
    name=package_name,
    version='0.0.0',
    # packages=find_packages(exclude=['test']),
    packages=[package_name],
    data_files=[
        (os.path.join('share', package_name, "launch"), glob('launch/*')),
        (os.path.join('share', package_name, "sound_file"), glob('sound_file/*')),
    ],
    # install_requires=['setuptools', 'whisper', 'pyaudio', 'playsound',],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sobits',
    maintainer_email='sobits@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    # tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "whisper_server = speech_recognition_whisper.whisper_server:main",
        ],
    },
)