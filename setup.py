from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'intro_to_ros'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
    ],
    install_requires=['setuptools','rclpy','mavros_msgs', 'numpy', 'mavros'],
    zip_safe=True,
    maintainer='aidan+andy+ken+roneet+shamak',
    maintainer_email='agao3019@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ['publisher = intro_to_ros.publisher:main',
                            'subscriber = intro_to_ros.subscriber:main',
                            'bluerov2_sensors = intro_to_ros.bluerov2_sensors:main',
                            'physics = intro_to_ros.physics_sim:main',
                            'armdisarm = intro_to_ros.armdisarm:main',
                            'dance = intro_to_ros.dance:main',
                            'pressure = intro_to_ros.pressure_to_depth:main',
                            "ros_bluerov2_interface = rosmav.ros_bluerov2_interface:main",
                            "pid_depth = intro_to_ros.pid_depth:main",
                            "pid_heading = intro_to_ros.pid_heading:main",
                            "camera_subscriber = intro_to_ros.camera_subscriber:main",
                            "flashing_lights = intro_to_ros.flashing_lights:main",
                            "mods = intro_to_ros.MODS:main",
                            "lane_subscriber = intro_to_ros.lane_subscriber:main"
        ],
    },
)
