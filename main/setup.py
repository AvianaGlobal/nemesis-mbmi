#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'numpy==1.16.6',
    'enaml==0.10.4',
    'enable==4.8.1'
    'chaco==4.8.0',
    'futures',
    'jsonpickle',
    'ibm_db_sa',
    'matplotlib==2.2.5',
    'pandas==0.24.2',
    'pyface==6.1.2',
    'pygments',
    'PySide',
    'pyzmq',
    'pyodbc',
    'PyQt4-windows-whl',
    'seaborn',
    'sqlalchemy',
    'traits==5.2.0',
    'traits-enaml==0.3.0',
    'traitsui==6.1.3',
    'rpy2==2.7.8',
]

setup_requirements = []

test_requirements = []

setup(
    author="AvianaGlobal",
    author_email='info@avianaglobal.com',
    python_requires='>=2.7',
    description="Nemesis Anomaly Detection System",
    package_data={
        'nemesis.app.builder': ['*.enaml'],
        'nemesis.app.common': ['*.enaml'],
        'nemesis.app.inspector': ['*.enaml'],
        'nemesis.app.inspector.plots': ['*.enaml'],
        'nemesis.data.ui': ['*.enaml'],
        'nemesis.r.ui': ['*.enaml'],
        'nemesis.stdlib.ui': ['*.enaml'],
        'nemesis.ui': ['*.enaml'],
    },
    entry_points={
        'console_scripts': [
            'nemesis-builder=nemesis.app.builder.main:main',
            'nemesis-inspector=nemesis.app.inspector.main:main',
        ],
    },
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
    keywords='nemesis',
    name='nemesis',
    packages=find_packages(include=['nemesis', 'nemesis.*', 'rparse']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/AvianaGlobal/nemesis-mbmi',
    version='0.1',
    zip_safe=True,
)
