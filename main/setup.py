from setuptools import setup, find_packages

setup(
    name='nemesis',
    version='0.1',
    author='AvianaGlobal',
    author_email='info@avianaglobal.com',
    packages=find_packages(),
    entry_points={
        'console_scripts': [],
        'gui_scripts': [
            'nemesis-builder = nemesis.app.builder.main:main',
            'nemesis-inspector = nemesis.app.inspector.main:main',
        ],
    }
)
