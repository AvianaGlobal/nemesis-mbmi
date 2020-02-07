from setuptools import setup, find_packages

setup(
    name='nemesis',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [

        ],
        'gui_scripts': [
            'elite-modeler = elite.app.builder.main:main',
            'elite-inspector = elite.app.inspector.main:main',
        ],
    }
)
