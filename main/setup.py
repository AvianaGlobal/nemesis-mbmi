from setuptools import setup, find_packages

setup(
    name='nemesis',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [

        ],
        'gui_scripts': [
            'nemesis-modeler = nemesis.app.builder.main:main',
            'nemesis-inspector = nemesis.app.inspector.main:main',
        ],
    }
)
