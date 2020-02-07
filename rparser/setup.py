from setuptools import setup, find_packages

setup(
    name='rparse',
    version='0.1',
    author='Elite Analytics LLC',
    url='http://www.eliteanalytics.com',
    description='Elite Analytics R parser',
    install_requires=[
        # 'pyzmq >= 16.0.2',
        # 'rpy2 >= 2.8.5',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'rparse = rparse.server:main'
        ],
    },
)
