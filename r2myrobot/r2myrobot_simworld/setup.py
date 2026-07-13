from setuptools import find_packages, setup

package_name = 'r2myrobot_simworld'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # install launch and params
        ('share/' + package_name + '/launch', [
            'launch/simworld.launch.py',
            'launch/demo.launch.py',
        ]),
        ('share/' + package_name + '/params', [
            'params/simworld_params.yaml',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='aufalamoe@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'simworld_node = r2myrobot_simworld.simworld_node:main',
            'demo_pose_publisher = r2myrobot_simworld.demo_pose_publisher:main',
            'map_point_bridge = r2myrobot_simworld.map_point_bridge:main',
        ],
    },
)
