# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='Bade',
    version='0.1',
    author='Martin Magr',
    author_email='mmagr@redhat.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'bade = bade.bade:bade',
        ],
    }
)
