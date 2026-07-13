import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'r2myrobot_2d'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
              (os.path.join('share', package_name, 'launch'),
        glob(os.path.join('launch', '*.launch.py'))),
              (os.path.join('share', package_name, 'worlds'),
        glob(os.path.join('worlds', '*.sdf'))),
              (os.path.join('share', package_name, 'rviz'),
        glob(os.path.join('rviz', '*.rviz'))),
              (os.path.join('share', package_name, 'hook'),
        glob('hook/*.sh')),*[(os.path.join('share', package_name, os.path.dirname(file_path)), [file_path]) 
              for file_path in glob(os.path.join('models', '**/*'), recursive=True) 
              if os.path.isfile(file_path)],
    ],
    zip_safe=True,
    maintainer='root',
    maintainer_email='aufalamoe@gmail.com',
    description='R2 2D',
    license='a',

    entry_points={
        'console_scripts': [
            'r2myrobot_2d_gui=r2myrobot_2d.main:main',
        ],
    },
)
